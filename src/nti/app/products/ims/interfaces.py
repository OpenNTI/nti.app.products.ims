#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from pyramid.interfaces import IRequest

from zope import interface

from zope.schema import ValidationError

from nti.app.products.ims import MessageFactory as _

from nti.ims.lti.interfaces import ITool


class ILTIRequest(IRequest):
    pass


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


class IOAuthProviderRequestValidator(interface.Interface):
    """
    An implementation of of oauthlib.oauth1.rfc5849.request_validator.RequestValidator
    that can be used to validate requests to SignatureOnlyEndpoints from ToolProviders.
    """


class IOAuthProviderSignatureOnlyEndpoint(interface.Interface):
    """
    An implementation of of oauthlib.oauth1.rfc5849.endpoints.signature_only
    that can be used to validate requests to using IOAuthProviderRequestValidator.
    """


class IOAuthNonceRecorder(interface.Interface):

    def record_nonce_received(nonce, expires=600):
        """
        Records the provided nonce as having been seen.
        If a nonce is reused within the provided expires
        time a key error is raised
        """


class ILTIUserFactory(interface.Interface):

    def user_for_request(request):
        """
        Looks up a user object for an LTIRequest
        If the specified user does not exist, create a user account for them

        :param LTIRequest
        :return User object
        """


class ILaunchParamsMapping(interface.Interface):
    """
    A mapping of launch request fields to package specific values
    e.g.
    'EXAMPLE_PACKAGE_ID': 'tool_consumer_instance_guid'
    """


class IInvalidLTISourcedIdException(interface.Interface):
    """
    An error that occurs while decoding a sourcedid.
    """


@interface.implementer(IInvalidLTISourcedIdException)
class InvalidLTISourcedIdException(ValidationError):
    __doc__ = _(u'Invalid outcomes result sourcedid.')
    i18n_message = __doc__
