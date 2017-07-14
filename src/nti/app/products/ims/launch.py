#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The module provides a basic lti launch tool implementation that allows
a tool consumer to launch the NT platform.  While this serves as a good
example producer, we could probably make an argument that this entire module
belongs somewhere like nti.appserver or nti.app
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lti.utils import InvalidLTIRequestError

from zope import component
from zope import interface

from pyramid import httpexceptions as hexc

from nti.app.products.ims.interfaces import IToolProvider

from nti.app.products.ims.provider import ToolProvider

from nti.appserver.interfaces import IApplicationSettings

from nti.appserver.policies.interfaces import ISitePolicyUserEventListener

from nti.ims.lti.interfaces import ITool


@interface.implementer(ITool)
class LaunchTool(object):
    """
    A simple tool that launches the platform, optionally targeting an ntiid
    """

    __name__ = 'launch'

    @property
    def site_policy_listener(self):
        return component.getUtility(ISitePolicyUserEventListener)

    @property
    def title(self):
        return u'Launch ' + getattr(self.site_policy_listener, 'BRAND', u'')

    @property
    def description(self):
        return self.title


def _web_root():
    settings = component.getUtility(IApplicationSettings)
    web_root = settings.get('web_app_root', '/NextThoughtWebApp/')
    return web_root


def _provider_factory(tool, request):
    return LaunchProvider.from_unpacked_request(None,
                                                request.params,
                                                request.url,
                                                request.headers)


NTIID_PARAM_NAME = 'nti_ntiid'


@interface.implementer(IToolProvider)
class LaunchProvider(ToolProvider):
    """
    A basic tool provider to handle responding to a consumer request
    to launch the NT platform.
    """

    tool = None

    @property
    def target_ntiid(self):
        try:
            return self.get_custom_param(NTIID_PARAM_NAME)
        except KeyError:
            return None

    @property
    def __name__(self):
        return self.tool.__name__

    @property
    def title(self):
        return self.tool.title

    @property
    def description(self):
        return self.tool.description

    @property
    def tool_url(self):
        return _web_root()

    def valid_request(self):
        super(LaunchProvider, self).valid_request()
        if not self.is_launch_request():
            raise InvalidLTIRequestError('Expected launch request')
