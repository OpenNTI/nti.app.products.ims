#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division

from zope.component import queryUtility

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lti.utils import InvalidLTIRequestError

from zope import component
from zope import interface

from zope.location.interfaces import IContained
from zope.location.interfaces import LocationError

from zope.location.location import LocationProxy

from zope.traversing.interfaces import IPathAdapter
from zope.traversing.interfaces import ITraversable

from pyramid import httpexceptions as hexc

from pyramid.response import Response

from pyramid.view import view_config

from nti.app.base.abstract_views import AbstractView, AbstractAuthenticatedView

from nti.app.products.ims import IMS
from nti.app.products.ims import LTI
from nti.app.products.ims import SIS
from nti.app.products.ims import TOOLS

from nti.app.products.ims.interfaces import ILTIUserFactory

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import IToolProvider

from nti.appserver.logon import _create_success_response

from nti.appserver.policies.interfaces import INoAccountCreationEmail

from nti.dataserver.interfaces import ILinkExternalHrefOnly

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

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
             request_method='POST',
             context=IConfiguredToolContainer,
             name='list_tools')
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
             name='create_tool')
class ConfiguredToolCreateView(AbstractView):

    def get_tools(self):
        return self.context

    def __call__(self):
        tool = IConfiguredTool(self.request)
        tools = self.get_tools()
        tools.add_tool(tool)
        return hexc.HTTPCreated('Successfully created tool')


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='POST',
             context=IConfiguredToolContainer,
             name='delete_tool')
class ConfiguredToolDeleteView(AbstractView):

    def __call__(self):
        name = self.request.title
        self.context.delete_tool(name)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='POST',
             context=IConfiguredToolContainer,
             name='edit_tool')
class ConfiguredToolEditView(AbstractView):

    def __call__(self):
        name = self.request.title
        self.context.edit_tool(name)
