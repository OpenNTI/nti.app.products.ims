#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from pyramid import httpexceptions as hexc

import urlparse

from zope import component
from zope import interface

from ims_lti_py.request_validator import RequestValidatorMixin
from ims_lti_py.tool_provider import ToolProvider

from nti.ims.lti.interfaces import IOAuthConsumers

class PyramidRequestValidatorMixin(RequestValidatorMixin):
    """
    A basic oauth tool provider for pyramid requests.
    This objects valid_request can be subclasses to provide
    additional verification
    """

    def parse_request(self, request, parameters=None, fake_method=None):
        '''
        Parse pyramid request object
        '''
        params = dict(parameters or request.params)
        return (request.method,
                request.url.rsplit('?', 1)[0],
                request.headers,
                params)

def _consumer(key, consumers=None):
    if key is None:
        return None

    if consumers is None:
        consumers = component.getUtility(IOAuthConsumers)
    return consumers[key]

class PyramidToolProvider(PyramidRequestValidatorMixin, ToolProvider):
    """
    A pyramid based tool provider
    """

    def __init__(self, request):
        if request.method != 'POST':
            raise ValueError('Expected POST')

        consumer = _consumer(request.params.get('oauth_consumer_key'))
        if not consumer:
            raise ValueError('No consumer key info provided')

        super(PyramidToolProvider, self).__init__(consumer.key, consumer.secret, request.params)

