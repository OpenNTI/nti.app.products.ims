#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from lti.outcome_request import OutcomeRequest

from lti.outcome_response import OutcomeResponse

from zope import component
from zope import interface

from zope.proxy import ProxyBase
from zope.proxy import non_overridable
from zope.proxy import getProxiedObject

from zope.proxy.decorator import SpecificationDecoratorBase

from nti.app.products.ims.interfaces import ILTIRequest

from nti.externalization.persistence import NoPickle

from nti.externalization.representation import WithRepr

from nti.ims.lti.interfaces import IOutcomeRequest
from nti.ims.lti.interfaces import IResultSourcedId
from nti.ims.lti.interfaces import IOutcomeReadRequest
from nti.ims.lti.interfaces import IOutcomeDeleteRequest
from nti.ims.lti.interfaces import IOutcomeReplaceRequest

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@NoPickle
@interface.implementer(IOutcomeRequest)
class OutcomeRequestProxy(SpecificationDecoratorBase):

    def __new__(cls, base, *unused_args, **unused_kwargs):
        return ProxyBase.__new__(cls, base)

    def __init__(self, base):
        ProxyBase.__init__(self, base)

    @non_overridable
    @property
    def result_id(self):
        sourcedid = unicode(self.lis_result_sourcedid)
        return ResultSourcedId(lis_result_sourcedid=sourcedid)

    @non_overridable
    def __call__(self):
        # TODO
        pass


@NoPickle
@interface.implementer(IOutcomeReplaceRequest)
class OutcomeReplaceRequestProxy(OutcomeRequestProxy):

    createDirectFieldProperties(IOutcomeReplaceRequest)

    def __new__(cls, base, *unused_args, **unused_kwargs):
        return ProxyBase.__new__(cls, base)

    def __init__(self, base, score):
        ProxyBase.__init__(self, base)
        self.score = score


def _get_score(obj):
    try:
        result = float(obj.score)
    except (TypeError, ValueError):
        # Want this to percolate up during schema validation
        result = obj.score
    return result


@component.adapter(ILTIRequest)
@interface.implementer(IOutcomeRequest)
def _create_outcome_request(request):
    outcome_request = OutcomeRequest.from_post_request(request)
    result = None
    if outcome_request.is_delete_request():
        result = OutcomeRequestProxy(outcome_request)
        interface.alsoProvides(result, IOutcomeDeleteRequest)
    elif outcome_request.is_read_request():
        result = OutcomeRequestProxy(outcome_request)
        interface.alsoProvides(result, IOutcomeReadRequest)
    elif outcome_request.is_replace_request():
        score = _get_score(outcome_request)
        result = OutcomeReplaceRequestProxy(outcome_request, score=score)
        interface.alsoProvides(result, IOutcomeReplaceRequest)
    return result


@WithRepr
@interface.implementer(IResultSourcedId)
class ResultSourcedId(SchemaConfigured):

    createDirectFieldProperties(IResultSourcedId)
