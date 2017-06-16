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

from zope import interface

from pyramid import httpexceptions as hexc

import urlparse

from zope import component
from zope import interface

from nti.appserver.interfaces import IApplicationSettings

from nti.appserver.policies.interfaces import ISitePolicyUserEventListener

from nti.ims.lti.config import ToolConfigFactory

from nti.ims.lti.interfaces import IOAuthConsumers
from nti.ims.lti.interfaces import ITool

from .interfaces import IToolProvider

from .provider import ToolProvider

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
        return 'Launch ' + self.site_policy_listener.BRAND

    @property
    def description(self):
        return self.title

class LaunchToolConfigFactory(ToolConfigFactory):
    """
    A launch tool config that makes sure canvas requests all user
    data and that the request from canvas is oauth compliant
    """

    def __init__(self, tool):
        super(LaunchToolConfigFactory, self).__init__(tool)

    def __call__(self):
        config = super(LaunchToolConfigFactory, self).__call__()

        # TODO Should probably pull these out into subscribers
        canvas_ext = {
            'oauth_compliant': 'true',
            'privacy_level': 'Public'
        }
        config.set_ext_params('canvas.instructure.com', canvas_ext)

        return config

def _web_root():
    settings = component.getUtility(IApplicationSettings)
    web_root = settings.get('web_app_root', '/NextThoughtWebApp/')
    return web_root

NTIID_PARAM_NAME = 'nti_ntiid'

def _provider_factory(tool, request):
    return LaunchProvider.from_unpacked_request(None,
                                                request.params,
                                                request.url,
                                                request.headers)


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

    def respond(self):
        # TODO seems like we should have some component/utility
        # somewhere that knows how to generate a web platform
        # url for an ntiid or id.  Regardless this probably
        # doesn't belong here.  We could spring board this through
        # another interface

        # TODO generate the url with the target_ntiid if we have one
        return hexc.HTTPSeeOther(location=_web_root())

    def valid_request(self):
        super(LaunchProvider, self).valid_request()
        if not self.is_launch_request():
            raise ValueError('Expected launch request')


