#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from bs4 import BeautifulSoup

from zope import component
from zope import interface

from nti.app.products.ims.interfaces import ILTIRequest

from nti.externalization.representation import WithRepr

from nti.ims.lti.interfaces import IOutcomeRequest
from nti.ims.lti.interfaces import IResultSourcedId
from nti.ims.lti.interfaces import IOutcomeReadRequest
from nti.ims.lti.interfaces import IOutcomeDeleteRequest
from nti.ims.lti.interfaces import IOutcomeReplaceRequest

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


def _get_doc_field_val(doc, field):
    field_val = doc.find(field)
    return field_val and field_val.text


def _get_delete_request(unused_doc, result_id):
    """
    <?xml version="1.0" encoding="UTF-8"?>
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
    return OutcomeDeleteRequest(result_id=result_id)


def _get_read_request(unused_doc, result_id):
    """
    <?xml version="1.0" encoding="UTF-8"?>
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
    return OutcomeReadRequest(result_id=result_id)


def _get_replace_request(doc, result_id):
    """
    <?xml version="1.0" encoding="UTF-8"?>
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
              <textString>0.92</textString>
            </resultScore>
          </result>
        </resultRecord>
      </replaceResultRequest>
    </imsx_POXBody>
    </imsx_POXEnvelopeRequest>
    """
    score_str = _get_doc_field_val(doc, 'textstring')
    try:
        score = float(score_str)
    except (TypeError, ValueError):
        # Let this percolate up as a validation error
        score = score_str
    return OutcomeReplaceRequest(result_id=result_id, score=score)


@component.adapter(ILTIRequest)
@interface.implementer(IOutcomeRequest)
def _create_outcome_request(request):
    # Oauth body signing
    result = None
    doc = BeautifulSoup(request.POST, 'lxml')
    result_id = _get_doc_field_val(doc, 'sourcedid')
    if doc.find('replaceresultrequest'):
        result = _get_replace_request(doc, result_id)
    elif doc.find('readresultrequest'):
        result = _get_read_request(doc, result_id)
    elif doc.find("deleteresultrequest"):
        result = _get_delete_request(doc, result_id)
    return result


@interface.implementer(IOutcomeRequest)
class AbstractOutcomeRequest(SchemaConfigured):

    createDirectFieldProperties(IOutcomeRequest)

    def __init__(self, result_id=None, *args, **kwargs):
        result_id = ResultSourcedId(lis_result_sourcedid=result_id)
        SchemaConfigured.__init__(self, result_id=result_id, *args, **kwargs)

    def __call__(self):
        #: TODO
        pass


@WithRepr
@interface.implementer(IOutcomeReadRequest)
class OutcomeReadRequest(AbstractOutcomeRequest):

    createDirectFieldProperties(IOutcomeReadRequest)


@WithRepr
@interface.implementer(IOutcomeDeleteRequest)
class OutcomeDeleteRequest(AbstractOutcomeRequest):

    createDirectFieldProperties(IOutcomeDeleteRequest)


@WithRepr
@interface.implementer(IOutcomeReplaceRequest)
class OutcomeReplaceRequest(AbstractOutcomeRequest):

    createDirectFieldProperties(IOutcomeReplaceRequest)


@WithRepr
@interface.implementer(IResultSourcedId)
class ResultSourcedId(SchemaConfigured):

    createDirectFieldProperties(IResultSourcedId)
