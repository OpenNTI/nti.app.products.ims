#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from oauthlib.oauth1.rfc5849.endpoints.signature_only import SignatureOnlyEndpoint

from oauthlib.oauth1.rfc5849.request_validator import RequestValidator

from oauthlib.oauth1.rfc5849.utils import UNICODE_ASCII_CHARACTER_SET

import transaction

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

from nti.app.products.ims.interfaces import IOAuthNonceRecorder
from nti.app.products.ims.interfaces import IOAuthRequestValidator
from nti.app.products.ims.interfaces import IOAuthProviderRequestValidator
from nti.app.products.ims.interfaces import IOAuthProviderSignatureOnlyEndpoint

from nti.dataserver.interfaces import IRedisClient

from nti.transactions.transactions import ObjectDataManager

from nti.ims.lti.interfaces import IOAuthConsumers
from nti.dataserver.metadata.index import get_metadata_catalog, IX_MIMETYPE
from nti.ims.lti.consumer import ConfiguredTool

LTI_NONCES = '++etc++ims++queue++nti_lti_nonces'

logger = __import__('logging').getLogger(__name__)


class _AbortingDataManager(ObjectDataManager):
    """
    A datamanager which, unlike it's superclass, calls
    the callable if the transaction aborts.

    RedisNonceRecorder records nonces into redis at check time,
    rather than waiting for our main transaction to commit,
    in order to avoid time-of-check/time-of-use attacks.  This
    datamanger calls the provided callable on rollback/abort
    so that the nonce can be cleared from redis in case we
    end up being retried
    """

    def tpc_finish(self, _):
        pass

    def _abort(self):
        self.callable(*self.args, **self.kwargs)

    def abort(self, _):
        self._abort()

    def rollback(self):
        self._abort()


class RedisNonceRecorder(object):
    """
    A redis backed implementation of IOAuthNonceVerifier
    """
    _redis = None

    def _redis_client(self):
        return self._redis or component.getUtility(IRedisClient)

    def record_nonce_received(self, nonce, expires=600):
        redis = self._redis_client()
        if redis.hexists(LTI_NONCES, nonce):
            raise KeyError(nonce)
        pipe = redis.pipeline()
        pipe.hset(LTI_NONCES, nonce, 1).expire(nonce, expires).execute()
        transaction.get().join(_AbortingDataManager(target=self,
                                                    method_name='rollback',
                                                    args=(redis, nonce)))

    def rollback(self, redis, nonce):
        redis.hdel(LTI_NONCES, nonce)


_DUMMY_CLIENT_KEY = u'_nti_dummy_client_key'
_DUMMY_CLIENT_SECRET = u'_nti_dummy_client_secret'

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
        return 20, 64  # At least canvas is producing nonces of len == 32

    @property
    def safe_characters(self):
        return _SAFE_CHARS

    def _consumer(self, key):
        consumers = component.getUtility(IOAuthConsumers)
        return consumers[key]

    @property
    def dummy_client(self):
        return _DUMMY_CLIENT_KEY

    # pylint: disable=arguments-differ

    def get_client_secret(self, client_key, unused_request):
        # Here client_key is something that has been returned as
        # valid according to validate_client_key or the default
        try:
            return self._consumer(client_key).secret
        except KeyError:
            # client_key should always be the dummy key here
            return _DUMMY_CLIENT_SECRET

    def validate_client_key(self, client_key, unused_request):
        try:
            return self._consumer(client_key) is not None
        except KeyError:
            return False

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None,
                                     access_token=None):
        try:
            nonces = component.getUtility(IOAuthNonceRecorder)
            nonces.record_nonce_received(nonce,
                                         expires=self.timestamp_lifetime)
            return True
        except KeyError:
            return False


@interface.implementer(IOAuthRequestValidator)
class DevModeOAuthValidator(OAuthSignatureOnlyValidator):
    enforce_ssl = False


def _get_tool_iter():
    # FIXME: Need to move towards registration
    catalog = get_metadata_catalog()
    rs = catalog.apply({IX_MIMETYPE: {'any_of': (ConfiguredTool.mime_type,)}})
    intids = component.getUtility(IIntIds)
    for result_intid in rs:
        obj = intids.queryObject(result_intid)
        if obj is not None:
            yield obj


@interface.implementer(IOAuthProviderRequestValidator)
class OAuthProviderRequestValidator(OAuthSignatureOnlyValidator):
    """
    An implementation of RequestValidator that implements
    the required methods for use with a SignatureOnlyEndpoint
    """

    def _configured_tool(self, key):
        for obj in _get_tool_iter():
            if obj.consumer_key == key:
                return obj

    def get_client_secret(self, client_key, unused_request):
        # Here client_key is something that has been returned as
        # valid according to validate_client_key or the default
        try:
            return self._configured_tool(client_key).secret
        except AttributeError:
            # client_key should always be the dummy key here
            return _DUMMY_CLIENT_SECRET

    def validate_client_key(self, client_key, unused_request):
        return self._configured_tool(client_key) is not None


@interface.implementer(IOAuthProviderRequestValidator)
class DevModeOAuthProviderRequestValidator(OAuthProviderRequestValidator):
    enforce_ssl = False


@interface.implementer(IOAuthProviderSignatureOnlyEndpoint)
def _get_endpoint_provider_request_validator():
    request_validator = component.getUtility(IOAuthProviderRequestValidator)
    return SignatureOnlyEndpoint(request_validator)
