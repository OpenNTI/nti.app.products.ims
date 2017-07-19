#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.interface import Attribute

from nti.ims.lti.interfaces import ITool


class ILTIRequest(interface.Interface):

    url = Attribute(u'The url of the lti request')

    params = Attribute(u'The parameters of the lti request')

    headers = Attribute(u'The headers of the lti request')


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


class ILTIUserFactory(interface.Interface):
    """
    Looks back through the launch params to find an adapter for a specific
    site package and can be used through user_for_request() to find a user object
    for the related provisioner
    """

    def user_for_request(launch_request):
        """
        Parse the launch request for relevant parameters and lookup a user
        If the specified user does not exist, create a user account for them
        :return User object
        """