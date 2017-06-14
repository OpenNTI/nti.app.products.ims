#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: views.py 104190 2017-01-12 20:20:37Z carlos.sanchez $
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from pyramid import httpexceptions as hexc

import urlparse

from zope import component
from zope import interface

from ims_lti_py.request_validator import RequestValidatorMixin
from ims_lti_py.tool_provider import ToolProvider

from .interfaces import IToolProvider

from nti.ims.lti.interfaces import IOAuthConsumers

def _query_params(url):
    parsed = urlparse.urlparse(url)
    return urlparse.parse_qs(parsed.query)

class PyramidRequestValidatorMixin(RequestValidatorMixin):
    '''
    A mixin for OAuth request validation using pyramid request
    '''
    def parse_request(self, request, parameters=None, fake_method=None):
        '''
        Parse pyramid request object
        '''
        params = dict(parameters or request.params)
        return (request.method,
                request.url.rsplit('?', 1)[0],
                request.headers,
                params)


@interface.implementer(IToolProvider)
class PyramidToolProvider(PyramidRequestValidatorMixin, ToolProvider):
    """
    A pyramid based tool provider
    """

    def __init__(self, request):
        if request.method != 'POST':
            raise ValueError('Expected POST')

        from IPython.core.debugger import Tracer;Tracer()()
        keys = component.getUtility(IOAuthConsumers)

        consumer_key = request.params['oauth_consumer_key']
        if not consumer_key:
            raise ValueError('Expected a consumer key')

        consumer_secret = keys[consumer_key].secret
        if not consumer_secret:
            raise ValueError('No consumer secret provided')

        super(PyramidToolProvider, self).__init__(consumer_key, consumer_secret, request.params)

