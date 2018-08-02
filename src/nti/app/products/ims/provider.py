#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from lti.utils import InvalidLTIRequestError

from lti.tool_provider import ToolProvider as LTIToolProvider

from zope import component

from nti.app.products.ims.interfaces import IOAuthRequestValidator

logger = __import__('logging').getLogger(__name__)


class ToolProvider(LTIToolProvider):
    """
    A pyramid based tool provider
    """

    def valid_request(self):
        validator = component.getUtility(IOAuthRequestValidator)
        if not super(ToolProvider, self).is_valid_request(validator):
            raise InvalidLTIRequestError('Invalid LTI Request')
        return True
