#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import contains_string

import fudge
import fakeredis
import requests

from lti.outcome_request import OutcomeRequest

from lti.utils import InvalidLTIConfigError

from requests_oauthlib import OAuth1

from requests_oauthlib.oauth1_auth import SIGNATURE_TYPE_AUTH_HEADER

from zope import component
from zope import interface

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import IOAuthProviderSignatureOnlyEndpoint

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.request_response import DummyRequest

from nti.ims.lti.consumer import ConfiguredTool

from nti.ims.lti.interfaces import IOutcomeRequest
from nti.ims.lti.interfaces import IOutcomeService
from nti.ims.lti.interfaces import IResultSourcedId
from nti.ims.lti.interfaces import IOutcomeReadRequest
from nti.ims.lti.interfaces import IOutcomeDeleteRequest
from nti.ims.lti.interfaces import IOutcomeReplaceRequest

from nti.coremetadata.interfaces import IRedisClient

from nti.testing.matchers import validly_provides


delete_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
        <imsx_POXHeader>
          <imsx_POXRequestHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
          </imsx_POXRequestHeaderInfo>
        </imsx_POXHeader>
        <imsx_POXBody>
          <deleteResultRequest>
            <resultRecord>
              <sourcedGUID>
                <sourcedId>3124567</sourcedId>
              </sourcedGUID>
            </resultRecord>
          </deleteResultRequest>
        </imsx_POXBody>
        </imsx_POXEnvelopeRequest>
        """


read_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">  <imsx_POXHeader>
        <imsx_POXRequestHeaderInfo>
          <imsx_version>V1.0</imsx_version>
          <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
        </imsx_POXRequestHeaderInfo>
        </imsx_POXHeader>
        <imsx_POXBody>
        <readResultRequest>
          <resultRecord>
            <sourcedGUID>
              <sourcedId>3124567</sourcedId>
            </sourcedGUID>
          </resultRecord>
        </readResultRequest>
        </imsx_POXBody>
        </imsx_POXEnvelopeRequest>
        """


replace_xml_fmt = """<?xml version="1.0" encoding="UTF-8"?>
        <imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
        <imsx_POXHeader>
          <imsx_POXRequestHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
          </imsx_POXRequestHeaderInfo>
        </imsx_POXHeader>
        <imsx_POXBody>
          <replaceResultRequest>
            <resultRecord>
              <sourcedGUID>
                <sourcedId>3124567</sourcedId>
              </sourcedGUID>
              <result>
                <resultScore>
                  <language>en</language>
                  <textString>%s</textString>
                </resultScore>
              </result>
            </resultRecord>
          </replaceResultRequest>
        </imsx_POXBody>
        </imsx_POXEnvelopeRequest>
        """

@interface.implementer(IOutcomeService)
class _MockOutcomeService(object):

    def __init__(self, sourcedid):
        self.sourcedid = sourcedid

    def get_score(self):
        return .42

    def set_score(self, unused_val):
        pass

    def remove_score(self):
        pass


class _MockOutcomeRequest(OutcomeRequest):

    def post_outcome_request(self, **kwargs):
        """
        Return the oauth1 signed request
        """
        if not self.has_required_attributes():
            raise InvalidLTIConfigError(
                'OutcomeRequest does not have all required attributes')
        header_oauth = OAuth1(self.consumer_key, self.consumer_secret,
                              signature_type=SIGNATURE_TYPE_AUTH_HEADER,
                              force_include_body=True, **kwargs)

        #headers = {b'HTTP_AUTHORIZATION': 'Bearer %s' % encoded_token}
        headers = {b'Content-type': b'application/xml'}
        result = requests.Request(method='POST',
                                  url=self.lis_outcome_service_url,
                                  headers=headers,
                                  auth=header_oauth,
                                  data=self.generate_request_xml())
        prepped = result.prepare()
        return requests.Request(method='POST',
                                url=self.lis_outcome_service_url,
                                headers=prepped.headers,
                                data=self.generate_request_xml())


class TestOutcomes(ApplicationLayerTest):

    def setUp(self):
        self.redis = fakeredis.FakeStrictRedis()
        gsm = component.getGlobalSiteManager()
        gsm.registerUtility(self.redis, IRedisClient)

    def tearDown(self):
        gsm = component.getGlobalSiteManager()
        gsm.unregisterUtility(self.redis, IRedisClient)

    @fudge.patch('nti.app.products.ims.oauth._get_tool_iter')
    def test_oauth_signature(self, mock_get_tools):
        consumer_key = u'0123456789abcdedfghijk'
        consumer_secret = u'consumer_secret'
        url = u'https://localhost:8082/dataserver2/lti/@@Outcomes'

        opts = {'consumer_key': consumer_key,
                'consumer_secret': consumer_secret,
                'lis_outcome_service_url': url,
                'operation': 'readResult',
                'lis_result_sourcedid': '123:456:789'}
        test_outcome_request = _MockOutcomeRequest(opts=opts)
        def _make_request():
            return test_outcome_request.post_read_result()

        sig_endpoint = component.getUtility(IOAuthProviderSignatureOnlyEndpoint)
        def _do_validate():
            request = _make_request()
            result = sig_endpoint.validate_request(request.url,
                                                   http_method='POST',
                                                   body=request.data,
                                                   headers=request.headers)
            return result

        # No tools
        mock_get_tools.is_callable().returns(())
        validate_result, unused_validate_request = _do_validate()
        assert_that(validate_result, is_(False))

        # No match
        tool = ConfiguredTool(consumer_key=u'dev.nextthought.com',
                              secret=u'blahblahblah')
        mock_get_tools.is_callable().returns((tool,))

        validate_result, unused_validate_request = _do_validate()
        assert_that(validate_result, is_(False))

        # Bad secret
        tool = ConfiguredTool(consumer_key=consumer_key,
                              secret=u'blahblahblah')
        mock_get_tools.is_callable().returns((tool,))
        validate_result, unused_validate_request = _do_validate()
        assert_that(validate_result, is_(False))

        # Correct
        tool = ConfiguredTool(consumer_key=consumer_key,
                              secret=consumer_secret)
        mock_get_tools.is_callable().returns((tool,))

        validate_result, unused_validate_request = _do_validate()
        assert_that(validate_result, is_(True))

    def test_read(self):
        request = DummyRequest()
        request.body = read_xml
        lti_request = ILTIRequest(request)
        outcome_request = IOutcomeRequest(lti_request)
        assert_that(outcome_request, validly_provides(IOutcomeReadRequest))
        assert_that(outcome_request.result_id, validly_provides(IResultSourcedId))
        assert_that(outcome_request.result_id.lis_result_sourcedid, is_(u'3124567'))

        response = outcome_request()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, '<textString>None</textString>')
        assert_that(response_xml, contains_string('readResultResponse'))

        component.provideAdapter(_MockOutcomeService, adapts=(IResultSourcedId,))
        try:
            response = outcome_request()
            response_xml = response.generate_response_xml()
            assert_that(response_xml, '<textString>.42</textString>')
            assert_that(response_xml, contains_string('readResultResponse'))
        finally:
            gsm = component.getGlobalSiteManager()
            gsm.unregisterAdapter(_MockOutcomeService,
                                  required=(IResultSourcedId,))

    def test_delete(self):
        request = DummyRequest()
        request.body = delete_xml
        lti_request = ILTIRequest(request)
        outcome_request = IOutcomeRequest(lti_request)
        assert_that(outcome_request, validly_provides(IOutcomeDeleteRequest))
        assert_that(outcome_request.result_id, validly_provides(IResultSourcedId))
        assert_that(outcome_request.result_id.lis_result_sourcedid, is_(u'3124567'))

        response = outcome_request()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('deleteResultResponse'))

        component.provideAdapter(_MockOutcomeService, adapts=(IResultSourcedId,))
        try:
            response = outcome_request()
            response_xml = response.generate_response_xml()
            assert_that(response_xml, contains_string('deleteResultResponse'))
        finally:
            gsm = component.getGlobalSiteManager()
            gsm.unregisterAdapter(_MockOutcomeService,
                                  required=(IResultSourcedId,))

    def test_replace(self):
        request = DummyRequest()
        request.body = replace_xml_fmt % '.5'
        lti_request = ILTIRequest(request)
        outcome_request = IOutcomeRequest(lti_request)
        assert_that(outcome_request, validly_provides(IOutcomeReplaceRequest))
        assert_that(outcome_request._get_score_val(), is_(.5))
        assert_that(outcome_request.result_id, validly_provides(IResultSourcedId))
        assert_that(outcome_request.result_id.lis_result_sourcedid, is_(u'3124567'))

        def test_response_without_outcome_service(req):
            response = req()
            response_xml = response.generate_response_xml()
            assert_that(response_xml, contains_string('replaceResultResponse'))
            assert_that(response_xml, contains_string('<imsx_codeMajor>failure</imsx_codeMajor>'))

        def test_response(req, success=True):
            component.provideAdapter(_MockOutcomeService, adapts=(IResultSourcedId,))
            success_str = 'success' if success else 'failure'
            code_str = '<imsx_codeMajor>%s</imsx_codeMajor>' % success_str
            try:
                response = req()
                response_xml = response.generate_response_xml()
                assert_that(response_xml, contains_string('replaceResultResponse'))
                assert_that(response_xml, contains_string(code_str))
            finally:
                gsm = component.getGlobalSiteManager()
                gsm.unregisterAdapter(_MockOutcomeService,
                                      required=(IResultSourcedId,))

        request.body = replace_xml_fmt % '1.0'
        outcome_request = IOutcomeRequest(ILTIRequest(request))
        assert_that(outcome_request._get_score_val(), is_(1.0))
        test_response_without_outcome_service(outcome_request)
        test_response(outcome_request)

        request.body = replace_xml_fmt % '0.0'
        outcome_request = IOutcomeRequest(ILTIRequest(request))
        assert_that(outcome_request._get_score_val(), is_(0.0))
        test_response_without_outcome_service(outcome_request)
        test_response(outcome_request)

        request.body = replace_xml_fmt % '1.1'
        outcome_request = IOutcomeRequest(ILTIRequest(request))
        test_response_without_outcome_service(outcome_request)
        test_response(outcome_request, success=False)

        request.body = replace_xml_fmt % '-0.1'
        outcome_request = IOutcomeRequest(ILTIRequest(request))
        test_response_without_outcome_service(outcome_request)
        test_response(outcome_request, success=False)

        request.body = replace_xml_fmt % 'a'
        outcome_request = IOutcomeRequest(ILTIRequest(request))
        test_response_without_outcome_service(outcome_request)
        test_response(outcome_request, success=False)
