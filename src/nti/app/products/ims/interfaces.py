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


class ILMSInfoValidator(interface.Interface):
    """
    Given a launch request, returns the site name for a specific LMS
    """

    def __call__(request):
        """
        :return: site name and lms name, or none
        """


class ISiteInfoValidator(interface.Interface):
    """
    Given a launch request, returns if the relevant info is present and well formed for a specific site
    """

    def __call__(request, name):
        """
        :return: Boolean if info is present for provisioning
        """


class IIMSSessionProvision(interface.Interface):
    """
    Provisions a session for a request
    """