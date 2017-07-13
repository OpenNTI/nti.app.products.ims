#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.component import queryAdapter

from lti.utils import InvalidLTIRequestError
from lti.tool_provider import ToolProvider as _ToolProvider

from nti.app.products.ims.interfaces import IOAuthRequestValidator
from nti.app.products.ims.interfaces import ISession
from nti.app.products.ims.request import Request


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

        request = Request(self.from_unpacked_request(None,
                                              request.params,
                                              request.url,
                                              request.headers))

        adapter = queryAdapter(request, ISession, request.source)

        # If there isn't a specific adapter (janux), default to SIS
        #if not adapter:
        adapter = queryAdapter(request, ISession)

        return adapter.begin_session(request)
