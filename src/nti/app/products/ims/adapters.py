#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lti import InvalidLTIRequestError

from nti.app.products.ims import MessageFactory as _

from nti.app.products.ims.interfaces import ILTIUserFactory

from nti.ims.lti import adapt_accounting_for_consumer


def user_factory_for_request(request):
    """
    Parses through the launch params of an lti request
    to find a user factory for the appropriate site package
    """

    user_factory = adapt_accounting_for_consumer(request, request, ILTIUserFactory)

    if user_factory is None:
        msg = _('No user factory was found for this consumer tool')
        raise InvalidLTIRequestError(msg)

    return user_factory
