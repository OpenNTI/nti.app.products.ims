#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

import nti
from hamcrest import assert_that, is_
from lti import ToolConsumer
from nti.app.products.ims.interfaces import IIMSInfoValidator, ILTIRequest
from zope.component import subscribers

__docformat__ = "restructuredtext en"


import unittest

from zope import interface

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
		            provides=".interfaces.IIMSInfoValidator" />
		            
		<subscriber factory=".tests.test_provisioning.FakeLMSBuilder"
		            for=".tests.test_provisioning.FakeLMS"
		            provides=".interfaces.IIMSInfoValidator" />
		            
	</configure>
</configure>

"""

@interface.implementer(ILTIRequest)
class FakeSite(object):

    title = u'My fake site'


@interface.implementer(IIMSInfoValidator)
class FakeSiteBuilder(object):

    def __init__(self, validator):
        pass

    def __call__(self, request):
        return True


@interface.implementer(ILTIRequest)
class FakeLMS(object):
    title = u'My fake site'


@interface.implementer(IIMSInfoValidator)
class FakeLMSBuilder(object):
    def __init__(self, validator):
        pass

    def __call__(self, request):
        return True


def _make_launch_request(key, secret):
    tc = ToolConsumer(key, secret, params={
        'lti_message_type': 'basic-lti-launch-request',
        'lti_version': 'LTI-1.0',
        'resource_link_id': 'linkid',
        'launch_url': 'http://localhost/dataserver2/IMS/LTI/TOOLS/launch',
    })
    return tc, tc.generate_launch_request()


class TestValidation(nti.testing.base.ConfiguringTestBase):

    def test_registered_adapter(self):

        self.configure_string(REGISTER_ADAPTER_STRING)
        _, request = _make_launch_request('does not', 'exist')

        request = ILTIRequest(request)

        from IPython.core.debugger import Tracer;Tracer()()
        subs = subscribers((request,), IIMSInfoValidator)

        assert_that(len(subs), is_(2))

        for subscriber in subs:
            assert_that(subscriber(), is_(True))



