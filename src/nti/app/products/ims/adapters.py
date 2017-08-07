#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lti import InvalidLTIRequestError


from zope import component
from zope import interface

from nti.app.products.ims import MessageFactory as _

from nti.app.products.ims.interfaces import ILTIRequest
from nti.app.products.ims.interfaces import ILTIUserFactory

from nti.ims.lti import adapt_accounting_for_consumer


@interface.implementer(ILTIUserFactory)
@component.adapter(ILTIRequest)
def user_factory_for_request(request):
    """
    Parses through the launch params of an lti request
    to find a user factory for the appropriate site package
    """
    user_factory = adapt_accounting_for_consumer(request, request, 
                                                 ILTIUserFactory)
    if user_factory is None:
        msg = _(u'No user factory was found for this consumer tool')
        raise InvalidLTIRequestError(msg)
    return user_factory
