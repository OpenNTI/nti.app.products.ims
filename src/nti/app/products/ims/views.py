#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lti import tool_config

from lti.utils import InvalidLTIRequestError

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

import requests

from xml.etree import ElementTree as ET

from zope import component
from zope import interface

from zope.location.interfaces import IContained
from zope.location.interfaces import LocationError

from zope.location.location import LocationProxy

from zope.publisher.interfaces.browser import IBrowserRequest

from zope.traversing.interfaces import IPathAdapter
from zope.traversing.interfaces import ITraversable

from nti.app.base.abstract_views import AbstractView
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.internalization import read_body_as_external_object

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims import MessageFactory as _

from nti.app.products.ims import IMS
from nti.app.products.ims import LTI
from nti.app.products.ims import SIS
from nti.app.products.ims import TOOLS

from nti.app.products.ims.interfaces import ILTIUserFactory

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import IToolProvider

from nti.app.products.ims._table_utils import LTIToolsTable

from nti.appserver.logon import _create_success_response

from nti.appserver.policies.interfaces import INoAccountCreationEmail

from nti.appserver.ugd_edit_views import UGDPutView

from nti.dataserver.interfaces import ILinkExternalHrefOnly

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.consumer import PersistentToolConfig

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IConfiguredToolContainer
from nti.ims.lti.interfaces import ITool
from nti.ims.lti.interfaces import IToolConfigFactory

from nti.links import render_link

from nti.links.links import Link

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


@interface.implementer(IPathAdapter, IContained)
class IMSPathAdapter(object):

    __name__ = IMS

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context

    def __getitem__(self, key):
        if key == LTI:
            return LTIPathAdapter(self, self.request)
        elif key == SIS:
            return SISPathAdapter(self, self.request)
        raise KeyError(key)


@interface.implementer(IPathAdapter, IContained)
class LTIPathAdapter(object):

    __name__ = LTI

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent


@interface.implementer(IPathAdapter, IContained)
class SISPathAdapter(object):

    __name__ = SIS

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent


@interface.implementer(ITraversable, IContained)
class ToolProvidersAdapter(object):

    __name__ = TOOLS

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent

    def traverse(self, key, _):
        provider = component.queryUtility(ITool, name=key)
        if not provider:
            raise LocationError(key)
        return LocationProxy(provider, self, key)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='GET',
             context=ITool,
             name="config")
class ExecuteProviderView(AbstractView):

    def __call__(self):
        request = self.request
        provider = self.context
        conf = IToolConfigFactory(provider)()

        launch_link = Link(provider)
        interface.alsoProvides(launch_link, ILinkExternalHrefOnly)
        if not conf.launch_url:
            conf.launch_url = request.relative_url(render_link(launch_link))
        if not conf.secure_launch_url:
            conf.secure_launch_url = conf.launch_url
        # TODO: seems like there should be a hook somewhere that we
        # can use to just return the config here and let the normal
        # rendering machinary call to_xml and set a content type?
        resp = request.response
        resp.content_type = 'application/xml'
        resp.body = conf.to_xml()
        return resp


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='POST',
             context=ITool)
class LaunchProviderView(AbstractView):

    def __call__(self):
        lti_request = ILTIRequest(self.request)
        try:
            provider = component.queryMultiAdapter((self.context, lti_request),
                                                   IToolProvider)
            if not provider:
                return hexc.HTTPNotFound()
            provider.valid_request()
        except InvalidLTIRequestError:
            logger.exception('Invalid LTI Request')
            return hexc.HTTPBadRequest()
        # Try to grab an account
        try:
            # Mark the request to not send an account creation email
            interface.alsoProvides(lti_request, INoAccountCreationEmail)
            user_factory = ILTIUserFactory(lti_request)
            user = user_factory.user_for_request(lti_request)
        except InvalidLTIRequestError:
            logger.exception('Invalid LTI Request')
            return hexc.HTTPBadRequest('Unknown tool consumer')
        try:
            user_id = user.username
        except LookupError:
            logger.exception('Failed to retrieve user name from user object')
            # Go ahead and let _create_success_response try lookup in case
            # there is a cookie
            user_id = None
        redirect_url = provider.tool_url
        return _create_success_response(self.request, user_id, redirect_url)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='GET',
             context=IConfiguredToolContainer)
class ConfiguredToolsGetView(AbstractAuthenticatedView):

    def get_tools(self):
        return self.context

    def __call__(self):
        tools = self.get_tools()
        result = LocatedExternalDict()
        items = [tool for tool in tools.values()]
        result[ITEMS] = items
        result[TOTAL] = result[ITEM_COUNT] = len(items)
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='POST',
             context=IConfiguredToolContainer,
             name='create')
class ConfiguredToolCreateView(AbstractAuthenticatedView, ModeledContentUploadRequestUtilsMixin):

    def get_tools(self):
        return self.context

    def __call__(self):
        tool = self.readCreateUpdateContentObject(self.remoteUser)
        config = _create_tool_config_from_request(self.request)
        tool.config = config
        tools = self.get_tools()
        tools.add_tool(tool)
        msg = _('Tool created successfully')
        return hexc.HTTPCreated(msg)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='DELETE',
             context=IConfiguredTool,
             name='delete')
class ConfiguredToolDeleteView(AbstractView):

    def get_tools(self):
        return self.context.__parent__

    def __call__(self):
        tools = self.get_tools()
        tools.delete_tool(self.context)
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='PUT',
             context=IConfiguredTool,
             name='edit')
class ConfiguredToolEditView(UGDPutView):

    def __call__(self):
        tool = super(ConfiguredToolEditView, self).__call__()
        tool.config = _create_tool_config_from_request(self.request)
        return hexc.HTTPOk("Successfully edited tool")


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_configured_tool_summary.pt',
             request_method='GET',
             context=IConfiguredToolContainer,
             name='list')
def list_tools(context, request):
    tool_table = LTIToolsTable(context, IBrowserRequest(request))
    tool_table.update()
    return {'table': tool_table}


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_create_configured_tool.pt',
             request_method='GET',
             name='create_view',
             context=IConfiguredToolContainer)
def create(context, request):
    return {'title': 'Create an LTI Configured Tool',
            'extension': '@@create',
            'method': 'POST',
            'redirect': request.resource_url(context, '@@list')}


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_create_configured_tool.pt',
             request_method='GET',
             name='edit_view',
             context=IConfiguredTool)
def edit(context, request):

    return {'title': 'Edit an LTI Configured Tool',
            'extension': '@@edit',
            'method': 'PUT',
            'redirect': request.resource_url(context.__parent__, '@@list')}


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_tool_config.pt',
             request_method='GET',
             name='tool_config_view',
             context=IConfiguredTool)
def view_config(context, request):
    config = context.config
    attributes = dict()
    for attr in tool_config.VALID_ATTRIBUTES:
        attributes[attr] = getattr(config, attr, None)

    return {'attrs': attributes}


def _create_tool_config_from_xml(xml_file):
    xml_tree = ET.parse(xml_file)
    root = xml_tree.getroot()
    xml_string = ET.tostring(root)

    pconfig = PersistentToolConfig(dict())
    pconfig.process_xml(xml_string)
    return pconfig


def _create_tool_config_from_request(request):
    parsed = read_body_as_external_object(request)
    config_type = parsed['formselector'].encode('ascii')
    # Create from xml if uploaded
    if config_type == 'xml_paste':
        config = PersistentToolConfig(dict())
        config.process_xml(parsed[config_type])
    # Retrieve and create from URL if provided
    elif config_type == 'xml_link':
        response = requests.get(parsed[config_type])
        # TODO check this works
        config = _create_tool_config_from_xml(response)
    # Manual creation
    else:
        config = PersistentToolConfig(parsed)

    return config
