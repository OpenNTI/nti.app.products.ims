#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from lti import InvalidLTIRequestError

from nti.app.products.ims import MessageFactory as _

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import ILTIUserFactory

from nti.ims.lti import adapt_accounting_for_consumer


@interface.implementer(ILTIUserFactory)
@component.adapter(ILTIRequest)
class LTIUserFactoryAdapter(object):

    def __init__(self, request):

        self.request = request

        self.adapter = adapt_accounting_for_consumer(request,
                                                     ILTIUserFactory)
        if not self.adapter:
            msg = _('No adapter was found for this consumer tool')
            raise InvalidLTIRequestError(msg)

    def user_for_request(self):
        return self.adapter.user_for_request()
