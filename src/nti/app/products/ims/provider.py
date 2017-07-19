#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from lti.utils import InvalidLTIRequestError

from lti.tool_provider import ToolProvider as LTIToolProvider

from nti.app.products.ims.interfaces import IOAuthRequestValidator


class ToolProvider(LTIToolProvider):
    """
    A pyramid based tool provider
    """

    def valid_request(self):
        validator = component.getUtility(IOAuthRequestValidator)
        if not super(ToolProvider, self).is_valid_request(validator):
            raise InvalidLTIRequestError('Invalid LTI Request')
        return True
