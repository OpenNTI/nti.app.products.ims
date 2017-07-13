#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division

from nti.appserver.interfaces import IApplicationSettings

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.component import queryAdapter

from pyramid import httpexceptions as hexc

from lti.utils import InvalidLTIRequestError

from lti.tool_provider import ToolProvider as _ToolProvider

from nti.app.products.ims.interfaces import IOAuthRequestValidator



def _web_root():
    settings = component.getUtility(IApplicationSettings)
    web_root = settings.get('web_app_root', '/NextThoughtWebApp/')
    return web_root

class ToolProvider(_ToolProvider):
    """
    A pyramid based tool provider
    """

    def valid_request(self):
        validator = component.getUtility(IOAuthRequestValidator)
        if not super(ToolProvider, self).is_valid_request(validator):
            raise InvalidLTIRequestError('Invalid LTI Request')
        return True

    def respond(self, request):

        request = self.from_unpacked_request(None,
                                              request.params,
                                              request.url,
                                              request.headers)

        source = request.consumer_key
        adapter = queryAdapter(request, ISessionType, source)

        # If there isn't a specific adapter (janux), default to SIS
        if not adapter:
            adapter = queryAdapter(request, ISessionType)

        return adapter.begin_session(request)
