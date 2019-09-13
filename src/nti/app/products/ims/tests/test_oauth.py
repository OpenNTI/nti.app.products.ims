#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import raises
from hamcrest import calling
from hamcrest import not_none
from hamcrest import assert_that

import unittest

import fakeredis

import transaction

from zope import component

from nti.app.products.ims.interfaces import IOAuthNonceRecorder
from nti.app.products.ims.interfaces import IOAuthRequestValidator

from nti.app.products.ims.oauth import _DUMMY_CLIENT_KEY
from nti.app.products.ims.oauth import _DUMMY_CLIENT_SECRET

from nti.app.products.ims.oauth import RedisNonceRecorder

from nti.ims.lti.interfaces import IOAuthConsumers

from nti.ims.lti.oauth import OAuthConsumer

from nti.app.products.ims.tests import SharedConfiguringTestLayer
from nti.app.products.ims.tests import NonDevModeConfiguringTestLayer

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans


class TestRedisNonceTracking(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def setUp(self):
        self.recorder = RedisNonceRecorder()
        self.recorder._redis = fakeredis.FakeStrictRedis()

    def tearDown(self):
        self.recorder._redis.flushall()

    def test_registered(self):
        assert_that(component.getUtility(IOAuthNonceRecorder), not_none())

    @WithMockDSTrans
    def test_recording(self):
        # we can record a nonce
        self.recorder.record_nonce_received('foo')
        # but trying to record it again raises a KeyError
        assert_that(calling(self.recorder.record_nonce_received).with_args('foo'),
                    raises(KeyError))

    @WithMockDSTrans
    def test_recording_aborted(self):
        self.recorder.record_nonce_received('foo')
        # If the transaction gets aborted the recorder should
        # revert and the nonce is available
        transaction.abort()
        transaction.begin()
        self.recorder.record_nonce_received('foo')


class TestValidator(unittest.TestCase):

    layer = NonDevModeConfiguringTestLayer

    unregister = set()

    def setUp(self):
        self.validator = component.getUtility(IOAuthRequestValidator)

    def tearDown(self):
        consumers = component.getUtility(IOAuthConsumers)
        while self.unregister:
            del consumers[self.unregister.pop()]

    def _register_consumer(self, key, secret, title=u'My Test Consumer'):
        consumer = OAuthConsumer(key=key, secret=secret, title=title)
        consumers = component.getUtility(IOAuthConsumers)
        consumers[consumer.key] = consumer
        self.unregister.add(consumer.key)
        return consumer

    def test_registered(self):
        assert_that(self.validator, is_(not_none()))

    def test_enforce_ssl(self):
        assert_that(self.validator.enforce_ssl, is_(True))

    def test_keys_with_dots(self):
        assert_that(self.validator.check_client_key('dev.nextthought.com'),
                    is_(True))

    def test_canvas_nonce_length(self):
        nonce = 'D558CF552A572A2DCA3AEAC43F0A2217'
        assert_that(self.validator.check_nonce(nonce))

    def test_validate_client_key(self):
        assert_that(self.validator.validate_client_key('dev.nextthought.com', None),
                    is_(False))

        self._register_consumer(u'dev.nextthought.com', u'blahblahblah')

        assert_that(self.validator.validate_client_key('dev.nextthought.com', None),
                    is_(True))

    def test_get_secret(self):
        assert_that(self.validator.get_client_secret(_DUMMY_CLIENT_KEY, None),
                    is_(_DUMMY_CLIENT_SECRET))

        consumer = self._register_consumer(u'dev.nextthought.com',
                                           u'blahblahblah')

        assert_that(self.validator.get_client_secret(consumer.key, None),
                    is_(consumer.secret))


class TestDevModeValidator(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def setUp(self):
        self.validator = component.getUtility(IOAuthRequestValidator)

    def test_registered(self):
        assert_that(self.validator, not_none())

    def test_ssl_not_required(self):
        assert_that(self.validator.enforce_ssl, is_(False))
