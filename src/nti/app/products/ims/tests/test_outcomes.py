#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import contains_string

from zope import component
from zope import interface

from nti.app.products.ims.interfaces import ILTIRequest

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.request_response import DummyRequest

from nti.ims.lti.interfaces import IOutcomeRequest
from nti.ims.lti.interfaces import IOutcomeService
from nti.ims.lti.interfaces import IResultSourcedId
from nti.ims.lti.interfaces import IOutcomeReadRequest
from nti.ims.lti.interfaces import IOutcomeDeleteRequest
from nti.ims.lti.interfaces import IOutcomeReplaceRequest

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

class TestOutcomes(ApplicationLayerTest):

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
