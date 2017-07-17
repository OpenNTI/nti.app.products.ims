#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

from hamcrest import assert_that, is_

from pyramid.testing import DummyRequest

from zope.component import subscribers

from zope import interface

from nti.app.products.ims.interfaces import ILaunchRequestValidator
from nti.app.products.ims.interfaces import ILTIRequest

from nti.app.products.ims.tests import SharedConfiguringTestLayer

import nti.testing.base


REGISTER_ADAPTER_STRING = u"""
<configure	xmlns="http://namespaces.zope.org/zope"
			xmlns:i18n="http://namespaces.zope.org/i18n"
			xmlns:zcml="http://namespaces.zope.org/zcml">

	<include package="zope.component" file="meta.zcml" />
	<include package="zope.security" file="meta.zcml" />
	<include package="zope.component" />
	<include package="zope.security" />

	<include package="nti.ims" />

	<configure>
		<subscriber factory=".tests.test_provisioning.FakeSiteBuilder"
		            for=".tests.test_provisioning.FakeSite"
		            provides=".interfaces.ILaunchRequestValidator" />
		            
		<subscriber factory=".tests.test_provisioning.FakeLMSBuilder"
		            for=".tests.test_provisioning.FakeLMS"
		            provides=".interfaces.ILaunchRequestValidator" />
		            
	</configure>
</configure>

"""

@interface.implementer(ILTIRequest)
class FakeSite(object):

    title = u'My fake site'


@interface.implementer(ILaunchRequestValidator)
class FakeSiteBuilder(object):

    def __init__(self, validator):
        pass

    def __call__(self, request):
        return True


@interface.implementer(ILTIRequest)
class FakeLMS(object):
    title = u'My fake site'


@interface.implementer(ILaunchRequestValidator)
class FakeLMSBuilder(object):
    def __init__(self, validator):
        pass

    def validate(self, launch_request):
        return True


class TestValidation(nti.testing.base.ConfiguringTestBase):

    layer = SharedConfiguringTestLayer

    def test_registered_subscriber(self):

        url = 'http://example.com'
        req = DummyRequest(url=url, params={'foo': 'bar'})

        lti_request = ILTIRequest(req)

        self.configure_string(REGISTER_ADAPTER_STRING)

        subs = subscribers((lti_request,), ILaunchRequestValidator)

        assert_that(len(subs), is_(2))

        for subscriber in subs:
            assert_that(subscriber(), is_(True))
