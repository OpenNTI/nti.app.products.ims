#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import unittest

from hamcrest import assert_that
from hamcrest import is_
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_entries

from pyramid.testing import DummyRequest

from . import SharedConfiguringTestLayer

from ..interfaces import ILTIRequest

class TestPyramidLTIRequest(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_pyramid_request(self):
        url = 'http://example.com'
        req = DummyRequest(url=url, params={'foo': 'bar'})

        lti_request = ILTIRequest(req)
        assert_that(lti_request, not_none())

        assert_that(lti_request.url, is_(url))
        assert_that(lti_request.params, has_entry('foo', 'bar'))

    def test_url_params_striped(self):
        url = 'http://example.com?custom=ntiid'
        req = DummyRequest(url=url, params={'foo': 'bar'})

        lti_request = ILTIRequest(req)

        assert_that(lti_request.url, is_('http://example.com'))
        assert_that(lti_request.params, has_entries('foo', 'bar'))

