#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import assert_that

from zope.schema.interfaces import ValidationError

from nti.app.products.ims.interfaces import ILTIRequest

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.request_response import DummyRequest

from nti.ims.lti.interfaces import IOutcomeRequest
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


class TestOutcomes(ApplicationLayerTest):

    def test_read(self):
        request = DummyRequest()
        request.body = read_xml
        lti_request = ILTIRequest(request)
        outcome_request = IOutcomeRequest(lti_request)
        assert_that(outcome_request, validly_provides(IOutcomeReadRequest))
        assert_that(outcome_request.result_id, validly_provides(IResultSourcedId))
        assert_that(outcome_request.result_id.lis_result_sourcedid, is_(u'3124567'))

    def test_delete(self):
        request = DummyRequest()
        request.body = delete_xml
        lti_request = ILTIRequest(request)
        outcome_request = IOutcomeRequest(lti_request)
        assert_that(outcome_request, validly_provides(IOutcomeDeleteRequest))
        assert_that(outcome_request.result_id, validly_provides(IResultSourcedId))
        assert_that(outcome_request.result_id.lis_result_sourcedid, is_(u'3124567'))

    def test_replace(self):
        request = DummyRequest()
        request.body = replace_xml_fmt % '.5'
        lti_request = ILTIRequest(request)
        outcome_request = IOutcomeRequest(lti_request)
        assert_that(outcome_request, validly_provides(IOutcomeReplaceRequest))
        assert_that(outcome_request.score, is_(.5))
        assert_that(outcome_request.result_id, validly_provides(IResultSourcedId))
        assert_that(outcome_request.result_id.lis_result_sourcedid, is_(u'3124567'))

        request.body = replace_xml_fmt % '1.0'
        outcome_request = IOutcomeRequest(ILTIRequest(request))
        assert_that(outcome_request.score, is_(1.0))

        request.body = replace_xml_fmt % '0.0'
        outcome_request = IOutcomeRequest(ILTIRequest(request))
        assert_that(outcome_request.score, is_(0.0))

        request.body = replace_xml_fmt % '1.1'
        with self.assertRaises(ValidationError):
            IOutcomeRequest(ILTIRequest(request))

        request.body = replace_xml_fmt % '-0.1'
        with self.assertRaises(ValidationError):
            IOutcomeRequest(ILTIRequest(request))

        request.body = replace_xml_fmt % 'a'
        with self.assertRaises(ValidationError):
            IOutcomeRequest(ILTIRequest(request))
