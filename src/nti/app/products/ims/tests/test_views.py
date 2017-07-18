#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division



__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import ends_with
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_entries

from zope import component
from zope import interface

from zope.component import getGlobalSiteManager

from lti.tool_config import ToolConfig

from lti.tool_consumer import ToolConsumer

from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.interfaces import IOAuthConsumers

from nti.ims.lti.oauth import OAuthConsumer

from nti.app.products.ims.interfaces import ISessionProvider, ILTIRequest

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.tests import mock_dataserver

ITEMS = StandardExternalFields.ITEMS
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


@interface.implementer(ISessionProvider)
@component.adapter(ILTIRequest)
class FakeSessionProvider(object):

    def __init__(self, launch_request):
        pass

    def establish_session(self, launch_request):
        return True


class TestToolViews(ApplicationLayerTest):
    """
    We use the concrete launch tool as a test case for our general views
    """

    default_origin = 'http://janux.ou.edu'

    def _register_consumer(self, key, secret, title=u'My Test Consumer'):
        consumer = OAuthConsumer(key=key, secret=secret, title=title)
        consumers = component.getUtility(IOAuthConsumers)
        consumers[consumer.key] = consumer
        return consumer

    @WithSharedApplicationMockDS(users=False, testapp=True)
    def test_config(self):
        res = self.testapp.get('/dataserver2/IMS/LTI/TOOLS/launch/@@config')
        conf = ToolConfig.create_from_xml(res.body)

        assert_that(conf.title, is_('Launch NextThought'))
        assert_that(conf.launch_url,
                    is_('http://localhost/dataserver2/IMS/LTI/TOOLS/launch'))

        assert_that(conf.secure_launch_url,
                    is_('http://localhost/dataserver2/IMS/LTI/TOOLS/launch'))

        assert_that(conf.extensions,
                    has_entry('canvas.instructure.com',
                              has_entries('privacy_level', 'Public',
                                          'oauth_compliant', 'true')))

    def _make_launch_request(self, key, secret):
        tc = ToolConsumer(key, secret, params={
            'lti_message_type': 'basic-lti-launch-request',
            'lti_version': 'LTI-1.0',
            'resource_link_id': 'linkid',
            'launch_url': 'http://localhost/dataserver2/IMS/LTI/TOOLS/launch',
            'tool_consumer_instance_guid': 'test',
        })
        return tc, tc.generate_launch_request()

    @WithSharedApplicationMockDS(users=False, testapp=True)
    def test_launch(self):
        _, request = self._make_launch_request('does not', 'exist')

        # A launch request with bad credentials 400s
        self.testapp.post(request.url,
                          headers=request.headers,
                          params=request.body,
                          status=400)

        with mock_dataserver.mock_db_trans(self.ds):
            consumer = self._register_consumer(u'foonextthoughtcom',
                                               u'supersecret')
            gsm = getGlobalSiteManager()
            gsm.registerAdapter(FakeSessionProvider, name='test')

        _, request = self._make_launch_request(consumer.key, consumer.secret)
        result = self.testapp.post(request.url,
                                   headers={}, 
                                   params=request.body, status=303)
        assert_that(result.location, ends_with('/NextThoughtWebApp/'))

        with mock_dataserver.mock_db_trans(self.ds):
            consumers = component.getUtility(IOAuthConsumers)
            del consumers[consumer.key]
            gsm.unregisterAdapter(FakeSessionProvider, name='test')
