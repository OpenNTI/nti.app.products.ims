#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from oauthlib.oauth1.rfc5849.request_validator import RequestValidator
from oauthlib.oauth1.rfc5849.utils import UNICODE_ASCII_CHARACTER_SET

from nti.coremetadata.interfaces import IRedisClient

from .interfaces import IOAuthRequestValidator
from .interfaces import IOAuthNonceRecorder

from nti.ims.lti.interfaces import IOAuthConsumers

LTI_NONCES = 'nti_lti_nonces'

class RedisNonceRecorder(object):
    """
    A redis backed implementation of IOAuthNonceVerifier
    """

    def _redis_client(self):
        return component.getUtility(IRedisClient)

    def record_nonce_received(self, nonce, expires=600):
        redis = self._redis_client()
        if redis.hexists(LTI_NONCES, nonce):
            raise KeyError(nonce)
        pipe = redis.pipeline()
        pipe.hset(LTI_NONCES, nonce, 1).expire(nonce, expires)
        pipe.execute()
        # TODO attach a datamanager we can use to rollback the redis
        # value if the transaction is aborted

_DUMMY_CLIENT_KEY = '_nti_dummy_client_key'
_DUMMY_CLIENT_SECRET = '_nti_dummy_client_secret'

_SAFE_CHARS = set(UNICODE_ASCII_CHARACTER_SET) | set('.')

@interface.implementer(IOAuthRequestValidator)
class OAuthSignatureOnlyValidator(RequestValidator):
    """
    An implementation of RequestValidator that implements
    the required methods for use with a SignatureOnlyEndpoint
    """

    enforce_ssl = True

    @property
    def client_key_length(self):
        return 10, 30

    @property
    def nonce_length(self):
        return 20, 64 #At least canvas is producing nonces of len == 32

    @property
    def safe_characters(self):
        return _SAFE_CHARS

    def _consumer(self, key):
        consumers = component.getUtility(IOAuthConsumers)
        return consumers[key]

    @property
    def dummy_client(self):
        return _DUMMY_CLIENT_KEY

    def get_client_secret(self, client_key, request):
        # Here client_key is something that has been returned as
        # valid according to validate_client_key or the default
        try:
            return self._consumer(client_key).secret
        except KeyError:
            #client_key should always be the dummy key here
            return _DUMMY_CLIENT_SECRET

    def validate_client_key(self, client_key, request):
        try:
            return self._consumer(client_key) is not None
        except KeyError:
            return False

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None,
                                     access_token=None):
        nonces = component.getUtility(IOAuthNonceRecorder)
        try:
            nonces.record_nonce_received(nonce, expires=self.timestamp_lifetime)
            return True
        except KeyError:
            return False


@interface.implementer(IOAuthRequestValidator)
class DevModeOAuthValidator(OAuthSignatureOnlyValidator):

    enforce_ssl = False





