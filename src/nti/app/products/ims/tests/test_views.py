#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import fudge

from hamcrest import is_
from hamcrest import ends_with
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_entries

from io import BytesIO

import os

from pyramid.response import Response

from xml.etree import ElementTree as ET

from zope import component
from zope import interface

from zope.component import getGlobalSiteManager

from lti.tool_config import ToolConfig

from lti.tool_consumer import ToolConsumer

from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.interfaces import IOAuthConsumers

from nti.ims.lti.oauth import OAuthConsumer

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import ILTIUserFactory

from nti.app.products.ims.views import _create_tool_config_from_request

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.users import User

from nti.dataserver.users.interfaces import IUserProfile

from nti.dataserver.tests import mock_dataserver

from nti.testing.matchers import verifiably_provides


ITEMS = StandardExternalFields.ITEMS
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

TEST_ADAPTER_NAME = u'test'


@interface.implementer(ILTIUserFactory)
@component.adapter(ILTIRequest)
class FakeUserFactory(object):

    def __init__(self, launch_request):
        self.request = launch_request

    def user_for_request(self, request):
        assert_that(request, verifiably_provides(ILTIRequest))
        ds = mock_dataserver.current_mock_ds
        return User.get_user(u'cald3307', ds)


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

    def _make_launch_request(self, key, secret, optional_params={}):
        launch_params = {
            'lti_message_type': 'basic-lti-launch-request',
            'lti_version': 'LTI-1.0',
            'resource_link_id': 'linkid',
            'launch_url': 'http://localhost/dataserver2/IMS/LTI/TOOLS/launch',
        }
        launch_params = self._merge_dicts(optional_params, launch_params)
        tc = ToolConsumer(key, secret, params=launch_params)
        return tc, tc.generate_launch_request()

    def _merge_dicts(self, x, y):
        z = x.copy()
        z.update(y)
        return z

    def __save_attributes(self, user, soonerID, OU4x4):
        result = False
        if     not getattr(user, 'soonerID', None) \
            or not getattr(user, 'OU4x4', None):
            # set attrs in user for legacy purposes
            setattr(user, 'OU4x4', OU4x4)
            setattr(user, 'soonerID', soonerID)
            # set values in profile
            ou_profile = IUserProfile(user, None)
            if ou_profile is not None:
                ou_profile.OU4x4 = OU4x4
                ou_profile.soonerID = soonerID
            result = True
        return result

    def __create_user(self, username,
                      password='temp001',
                      soonerID=None,
                      OU4x4=None,
                      **kwargs):
        ds = mock_dataserver.current_mock_ds
        user = User.create_user(ds, username=username,
                                password=password, **kwargs)
        self.__save_attributes(user, soonerID, OU4x4)
        return user

    def _setup_mock(self, adapter_name=TEST_ADAPTER_NAME):
        with mock_dataserver.mock_db_trans(self.ds):
            self.consumer = self._register_consumer(u'foonextthoughtcom',
                                                    u'supersecret')

            self.gsm = getGlobalSiteManager()
            self.gsm.registerAdapter(FakeUserFactory, name=adapter_name)

    def _setup_user(self):
        with mock_dataserver.mock_db_trans(self.ds):
            self.__create_user(username=u'cald3307',
                               soonerID=u'112133307',
                               OU4x4=u'cald3307',
                               external_value={'realname': u'Carlos Sanchez',
                                               'email': u'foo@bar.com'},
                               meta_data={'check_4x4': False})

    def _teardown_mock(self, adapter_name=TEST_ADAPTER_NAME):
        with mock_dataserver.mock_db_trans(self.ds):
            consumers = component.getUtility(IOAuthConsumers)
            del consumers[self.consumer.key]
            self.gsm.unregisterAdapter(FakeUserFactory, name=adapter_name)

    @WithSharedApplicationMockDS(users=False, testapp=True)
    def test_launch(self):
        _, request = self._make_launch_request('does not', 'exist')

        self._setup_mock()
        self._setup_user()

        # A launch request with bad credentials 400s
        self.testapp.post(request.url,
                          headers=request.headers,
                          params=request.body,
                          status=400)

        _, request = self._make_launch_request(self.consumer.key, self.consumer.secret,
                                               {'tool_consumer_instance_guid': TEST_ADAPTER_NAME})

        result = self.testapp.post(request.url,
                                   headers={},
                                   params=request.body, status=303)
        assert_that(result.location, ends_with('/NextThoughtWebApp/'))

        self._teardown_mock()

    def _test_provisioning_result(self, result, keys={}):
        _, request = self._make_launch_request(
            self.consumer.key, self.consumer.secret, keys)

        self.testapp.post(request.url,
                          headers={},
                          params=request.body,
                          status=result)

    @WithSharedApplicationMockDS(users=False, testapp=True)
    def test_provisioning_adapters(self):
        self._setup_mock()
        self._setup_user()

        # A launch request with the tool_instance_guid we don't have
        self._test_provisioning_result(400)

        # A lr with tool_consumer_instance_guid we don't have and
        # tool_consumer_instance_url we do have
        keys = {'tool_consumer_instance_guid': 'dne',
                'tool_consumer_instance_url': TEST_ADAPTER_NAME}
        self._test_provisioning_result(303, keys)

        # Test tci name
        keys = {'tool_consumer_instance_guid': 'dne',
                'tool_consumer_instance_name': TEST_ADAPTER_NAME}
        self._test_provisioning_result(303, keys)

        # Test tc family code
        keys = {'tool_consumer_instance_guid': 'dne',
                'tool_consumer_info_product_family_code': TEST_ADAPTER_NAME}
        self._test_provisioning_result(303, keys)

        # Test everything being trash
        keys = {'tool_consumer_instance_guid': 'dne',
                'tool_consumer_instance_url': 'fake',
                'tool_consumer_instance_name': 'creative value',
                'oauth_consumer_key': 'nti',
                'tool_consumer_info_product_family_code': 'last_test'}

        self._test_provisioning_result(400, keys)

        self._teardown_mock()
        self._setup_mock(u'foonextthoughtcom')
        # Test consumer key
        keys = {'tool_consumer_instance_guid': 'dne'}
        self._test_provisioning_result(303, keys)
        self._teardown_mock(u'foonextthoughtcom')

    @fudge.patch('nti.app.products.ims.views.requests.get',
                 'nti.app.products.ims.views.read_body_as_external_object')
    def test_xml_download_(self, mock_response, mock_read):

        response = Response()
        response.content_encoding = 'identity'
        response.content_type = 'text/xml; charset=UTF-8'
        filename = 'ltitest.xml'
        response.content_disposition = 'attachment; filename="%s"' % filename

        stream = BytesIO()
        file_path = os.path.join(os.path.dirname(__file__), 'ltitest.xml')
        tree = ET.parse(file_path)
        tree.write(stream)

        stream.seek(0)
        stream.flush()
        response.body_file = stream

        fake_response = mock_response.is_callable()
        fake_response.returns(response)

        fake_read = mock_read.is_callable()
        fake_read.returns({'formselector': 'xml_link',
                           'xml_link': 'doesnt matter'})

        config = _create_tool_config_from_request(None)

        assert_that(config.title, is_('Qa Tool'))
        assert_that(config.description, is_('stool'))
        assert_that(config.launch_url, is_('https://lti.tools/saltire/tp'))

    def test_content_selection(self):
        pass

