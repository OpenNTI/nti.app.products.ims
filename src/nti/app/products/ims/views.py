#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import gevent

from lti import tool_config

from lti.utils import InvalidLTIRequestError

from lxml.etree import LxmlSyntaxError # pylint: disable=no-name-in-module

from pyramid import httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from pyramid.view import view_config

import requests

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

from nti.app.externalization.error import handle_possible_validation_error
from nti.app.externalization.error import raise_json_error

from nti.app.externalization.internalization import read_body_as_external_object

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims import MessageFactory as _

from nti.app.products.ims import IMS
from nti.app.products.ims import LTI
from nti.app.products.ims import SIS
from nti.app.products.ims import TOOLS
from nti.app.products.ims import VIEW_LTI_OUTCOMES

from nti.app.products.ims._table_utils import LTIToolsTable

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import IToolProvider
from nti.app.products.ims.interfaces import ILTIUserFactory
from nti.app.products.ims.interfaces import IInvalidLTISourcedIdException
from nti.app.products.ims.interfaces import IOAuthProviderSignatureOnlyEndpoint

from nti.appserver.logon import _create_success_response

from nti.appserver.policies.interfaces import INoAccountCreationEmail

from nti.appserver.ugd_edit_views import UGDPutView

from nti.base._compat import bytes_

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import ILinkExternalHrefOnly
from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.consumer import PersistentToolConfig

from nti.ims.lti.interfaces import ITool
from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IOutcomeRequest
from nti.ims.lti.interfaces import IToolConfigFactory
from nti.ims.lti.interfaces import IConfiguredToolContainer

from nti.links import render_link

from nti.links.links import Link

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


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
            # pylint: disable=too-many-function-args
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
             context=IConfiguredToolContainer,
             permission=nauth.ACT_CONTENT_EDIT)
class ConfiguredToolsGetView(AbstractAuthenticatedView):

    def get_tools(self):
        return self.context

    def __call__(self):
        tools = self.get_tools()
        result = LocatedExternalDict()
        items = []
        # pylint: disable=no-member
        for tool in tools.values():
            if IDeletedObjectPlaceholder.providedBy(tool):
                continue
            items.append(tool)
        result[ITEMS] = items
        result[TOTAL] = result[ITEM_COUNT] = len(items)
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='POST',
             context=IConfiguredToolContainer,
             permission=nauth.ACT_CONTENT_EDIT)
class ConfiguredToolCreateView(AbstractAuthenticatedView,
                               ModeledContentUploadRequestUtilsMixin):

    def get_tools(self):
        return self.context

    def readInput(self, value=None):
        result = super(ConfiguredToolCreateView, self).readInput(value)
        config = _create_tool_config_from_request(self.request)
        result[u'config'] = config
        return result

    def __call__(self):
        try:
            tool = self.readCreateUpdateContentObject(self.remoteUser)
        except Exception as e:  # pylint: disable=broad-except
            handle_possible_validation_error(self.request, e)
        # pylint: disable=no-member
        tools = self.get_tools()
        tools.add_tool(tool)
        msg = _(u'Tool created successfully')
        return hexc.HTTPCreated(msg)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='DELETE',
             context=IConfiguredTool,
             permission=nauth.ACT_CONTENT_EDIT)
class ConfiguredToolDeleteView(AbstractAuthenticatedView):

    def get_tools(self):
        # pylint: disable=no-member
        return self.context.__parent__

    def __call__(self):
        if not IDeletedObjectPlaceholder.providedBy(self.context):
            interface.alsoProvides(self.context, IDeletedObjectPlaceholder)
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='PUT',
             context=IConfiguredTool,
             permission=nauth.ACT_CONTENT_EDIT)
class ConfiguredToolEditView(UGDPutView):

    def readInput(self, value=None):
        result = super(ConfiguredToolEditView, self).readInput(value)
        config = _create_tool_config_from_request(self.request)
        result[u'config'] = config
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_configured_tool_summary.pt',
             request_method='GET',
             context=IConfiguredToolContainer,
             name='list',
             permission=nauth.ACT_READ)
def list_tools(context, request):
    tools = dict()
    for (key, value) in context.items():
        if IDeletedObjectPlaceholder.providedBy(value):
            continue
        tools[key] = value
    tool_table = LTIToolsTable(tools, IBrowserRequest(request))
    tool_table.update()
    return {'table': tool_table}


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_create_configured_tool.pt',
             request_method='GET',
             name='create_view',
             context=IConfiguredToolContainer,
             permission=nauth.ACT_CREATE)
def create(context, request):
    return {'title': 'Create an LTI Configured Tool',
            'url': request.resource_url(context),
            'method': 'POST',
            'redirect': request.resource_url(context, '@@list')}


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_create_configured_tool.pt',
             request_method='GET',
             name='edit_view',
             context=IConfiguredTool,
             permission=nauth.ACT_UPDATE)
def edit(context, request):

    return {'title': 'Edit an LTI Configured Tool',
            'method': 'PUT',
            'url': request.resource_url(context),
            'redirect': request.resource_url(context.__parent__, '@@list'),
            'tool_title': context.title}  # Has to be specified or create will fill with an object name


@view_config(route_name='objects.generic.traversal',
             renderer='templates/lti_tool_config.pt',
             request_method='GET',
             name='tool_config_view',
             context=IConfiguredTool,
             permission=nauth.ACT_READ)
def view_config_attributes(context, unused_request):
    config = context.config
    attributes = dict()
    for attr in tool_config.VALID_ATTRIBUTES:
        attributes[attr] = getattr(config, attr, None)
    return {'attrs': attributes}


def _raise_error(data, factory=hexc.HTTPBadRequest, request=None):
    request = request or get_current_request()
    raise_json_error(request, factory, data, None)


def _create_tool_config_from_request(request):
    parsed = read_body_as_external_object(request)
    config_type = parsed['formselector']
    # Create from xml if uploaded
    if config_type == u'xml_paste':
        try:
            config = PersistentToolConfig.create_from_xml(bytes_(parsed[config_type]))  # This has to be string type
        except LxmlSyntaxError:
            logger.exception('Bad xml config provided')
            _raise_error({'code': 'InvalidConfigurationXML',
                          'field': 'xml_paste',
                          'message': _('Invalid configuration XML.')
                         },
                         request=request)

    # Retrieve and create from URL if provided
    elif config_type == u'xml_link':
        with gevent.Timeout(3, hexc.HTTPGatewayTimeout):
            try:
                response = requests.get(parsed[config_type])
                response.raise_for_status()
            except ValueError:
                _raise_error({'code': 'InvalidToolConfigURL',
                              'field': 'xml_link',
                              'message': _('Invalid Tool Config URL.')
                             },
                             factory=hexc.HTTPUnprocessableEntity,
                             request=request)
            except:
                _raise_error({'code': 'InvalidToolConfigURL',
                              'field': 'xml_link',
                              'message': 'Unable to reach %s' % parsed[config_type]
                             },
                             factory=hexc.HTTPBadGateway,
                             request=request)
        try:
            config = PersistentToolConfig.create_from_xml(response.content)
        except LxmlSyntaxError:
            _raise_error({'code': 'InvalidToolConfigURL',
                          'field': 'xml_link',
                          'message': _('Invalid configuration from URL.')
                         },
                         factory=hexc.HTTPBadRequest,
                         request=request)
    # Manual creation
    else:
        config = PersistentToolConfig(**parsed)
    return config


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=LTIPathAdapter,
             name=VIEW_LTI_OUTCOMES,
             request_method='POST')
class OutcomePostbackView(AbstractView):

    def __call__(self):
        lti_request = ILTIRequest(self.request)
        outcome_request = IOutcomeRequest(lti_request)
        result_sourcedid = outcome_request.result_id
        __traceback_info__ = result_sourcedid, self.request.body
        try:
            # Used for logging, this will also validate the sourcedid.
            tool = IConfiguredTool(result_sourcedid, None)
        except IInvalidLTISourcedIdException:
            logger.exception("Invalid lis sourcedid (%s) (%s)",
                             result_sourcedid, self.request.body)
            return hexc.HTTPBadRequest()

        sig_endpoint = component.getUtility(IOAuthProviderSignatureOnlyEndpoint)
        is_valid, unused_request = sig_endpoint.validate_request(self.request.url,
                                                                 http_method='POST',
                                                                 body=self.request.body,
                                                                 headers=self.request.headers)

        if not is_valid:
            logger.info("Invalid LTI outcome (%s) (%s)",
                        result_sourcedid, tool.consumer_key)
            return hexc.HTTPBadRequest()

        # Create a response
        response = outcome_request()
        self.request.response.text = unicode(response.generate_response_xml())
        self.request.response.content_type = 'application/xml'
        self.request.response.charset = 'utf-8'
        self.request.response.status_code = 200
        return self.request.response
