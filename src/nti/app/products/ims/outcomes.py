#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import uuid

from lti.outcome_request import OutcomeRequest

from lti.outcome_response import OutcomeResponse

from zope import component
from zope import interface

from zope.container.contained import Contained

from zope.proxy import ProxyBase
from zope.proxy import non_overridable

from zope.proxy.decorator import SpecificationDecoratorBase

from zope.schema.interfaces import ValidationError

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import IUserOutcomeResult
from nti.app.products.ims.interfaces import IOutcomeResultContainer
from nti.app.products.ims.interfaces import IUserOutcomeResultContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.persistence import NoPickle

from nti.ims.lti.interfaces import IOutcomeService
from nti.ims.lti.interfaces import IOutcomeRequest
from nti.ims.lti.interfaces import IResultSourcedId
from nti.ims.lti.interfaces import IOutcomeReadRequest
from nti.ims.lti.interfaces import IOutcomeDeleteRequest
from nti.ims.lti.interfaces import IOutcomeReplaceRequest

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@NoPickle
@interface.implementer(IOutcomeRequest)
class AbstractOutcomeRequestProxy(SpecificationDecoratorBase):

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
    @property
    def msg_id(self):
        return str(uuid.uuid4().time_low)


@NoPickle
@interface.implementer(IOutcomeReplaceRequest)
class OutcomeReplaceRequestProxy(AbstractOutcomeRequestProxy):

    createDirectFieldProperties(IOutcomeReplaceRequest)

    def _get_score_val(self):
        try:
            result = float(self.score)
        except (TypeError, ValueError):
            result = None
        return result

    @non_overridable
    def __call__(self):
        service = IOutcomeService(self.result_id, None)
        score_val = self._get_score_val()
        try:
            self.score_val = score_val
        except ValidationError:
            score_val = None
        if score_val is None:
            logger.info("Invalid score (%s) (%s)",
                        self.result_id, self.score)
            code_major = 'failure'
        elif service is None:
            logger.info("Could not find outcome service (%s) (%s)",
                        self.result_id, self.score)
            code_major = 'failure'
        else:
            logger.debug('Setting score val (%s) (%s)',
                         self.result_id, self.score)
            service.set_score(score_val)
            code_major = 'success'
        desc = 'Score for %s set to %s (%s)' % (self.lis_result_sourcedid,
                                                self.score,
                                                code_major)
        result = OutcomeResponse(operation=self.operation,
                                 severity='status',
                                 description=desc,
                                 message_identifier=self.msg_id,
                                 message_ref_identifier=self.message_identifier,
                                 code_major=code_major)
        return result


@NoPickle
@interface.implementer(IOutcomeReadRequest)
class OutcomeReadRequestProxy(AbstractOutcomeRequestProxy):

    createDirectFieldProperties(IOutcomeReadRequest)

    @non_overridable
    def __call__(self):
        service = IOutcomeService(self.result_id, None)
        score = None
        if service is not None:
            score = service.get_score()
            score = str(score)
        result = OutcomeResponse(operation=self.operation,
                                 severity='status',
                                 message_identifier=self.msg_id,
                                 description='Score read successfully',
                                 message_ref_identifier=self.message_identifier,
                                 score=score)
        return result


@NoPickle
@interface.implementer(IOutcomeDeleteRequest)
class OutcomeDeleteRequestProxy(AbstractOutcomeRequestProxy):

    createDirectFieldProperties(IOutcomeDeleteRequest)

    @non_overridable
    def __call__(self):
        service = IOutcomeService(self.result_id, None)
        if service is not None:
            service.remove_score()
        result = OutcomeResponse(operation=self.operation,
                                 severity='status',
                                 message_identifier=self.msg_id,
                                 description='Score deleted successfully',
                                 message_ref_identifier=self.message_identifier)
        return result


@component.adapter(ILTIRequest)
@interface.implementer(IOutcomeRequest)
def _create_outcome_request(request):
    outcome_request = OutcomeRequest.from_post_request(request)
    result = None
    if outcome_request.is_delete_request():
        result = OutcomeDeleteRequestProxy(outcome_request)
    elif outcome_request.is_read_request():
        result = OutcomeReadRequestProxy(outcome_request)
    elif outcome_request.is_replace_request():
        result = OutcomeReplaceRequestProxy(outcome_request)
    return result


@interface.implementer(IResultSourcedId)
class ResultSourcedId(SchemaConfigured):

    createDirectFieldProperties(IResultSourcedId)

    def __str__(self):
        return "%s(%r)" \
                % (self.__class__.__name__, self.lis_result_sourcedid)
    __repr__ = __str__


@interface.implementer(IUserOutcomeResult)
class UserOutcomeResult(PersistentCreatedModDateTrackingObject,
                        Contained,
                        SchemaConfigured):

    createDirectFieldProperties(IUserOutcomeResult)

    __parent__ = None
    __name__ = None
    _item_ntiid = None

    item_ntiid = alias('ItemNTIID')

    mimeType = mime_type = "application/vnd.nextthought.ims.useroutcomeresult"

    def __str__(self):
        return "%s(%s %s %s)" \
                % (self.__class__.__name__,
                   self.ItemNTIID,
                   self.score,
                   self.ResultDate)
    __repr__ = __str__


@interface.implementer(IUserOutcomeResultContainer)
class UserOutcomeResultContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer):

    def pop(self, key, default=None):
        try:
            result = self[key]
            del self[key]
        except KeyError:
            result = default
        return result


@interface.implementer(IOutcomeResultContainer)
class OutcomeResultContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer):

    def pop(self, key, default=None):
        try:
            result = self[key]
            del self[key]
        except KeyError:
            result = default
        return result
