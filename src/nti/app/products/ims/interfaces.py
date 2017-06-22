#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: views.py 104190 2017-01-12 20:20:37Z carlos.sanchez $
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.interface import Attribute

from nti.ims.lti.interfaces import ITool

class ILTIRequest(interface.Interface):

    params = Attribute('The parameters of the lti request')

    url = Attribute('The url of the lti request')

    headers = Attribute('The headers of the lti request')


class IToolProvider(ITool):
    """
    An object that can validate and respond to launch request
    from an lti tool consumer.
    """

    def valid_request():
        """
        Validates the provided request is a valid LTI
        oauth request.
        """

    def respond():
        """
        Creates a response / renderable object that should
        be used to launch the tool.  The return value
        from this function should be suitable for returning
        from a view callable
        """

class IOAuthRequestValidator(interface.Interface):
    """
    An implementation of of oauthlib.oauth1.rfc5849.request_validator.RequestValidator
    that can be used to validate requests to SignatureOnlyEndpoint
    """

class IOAuthNonceRecorder(interface.Interface):

    def record_nonce_received(nonce, expires=600):
        """
        Records the provided nonce as having been seen.
        If a nonce is reused within the provided expires
        time a key error is raised
        """

