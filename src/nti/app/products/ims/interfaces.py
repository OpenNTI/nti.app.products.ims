#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division

from nti.schema.field import ValidTextLine

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

    def respond(request):
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


class ISession(interface.Interface):

    source = Attribute(u'Consumer key')

    resource_url = Attribute(u'Resource url being requested')

    user_id = Attribute(u'ID of user the session is issued to')

    timeframe = Attribute(u'Lifespan of the session')


class ISessionFactory(ISession):

    def begin_session(request):
        """
        Initializes a session and returns the appropriate content
        """

class IRequest(interface.Interface):
    """
    Consumer request
    """
