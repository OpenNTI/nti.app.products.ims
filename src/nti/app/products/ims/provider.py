#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from pyramid import httpexceptions as hexc

import urlparse

from zope import component
from zope import interface

from zope.interface import Attribute

from lti.utils import InvalidLTIRequestError

from lti.tool_provider import ToolProvider as _ToolProvider

from nti.ims.lti.interfaces import IOAuthConsumers

from .interfaces import IOAuthRequestValidator

class ToolProvider(_ToolProvider):
    """
    A pyramid based tool provider
    """

    def valid_request(self):
        validator = component.getUtility(IOAuthRequestValidator)
        if not super(ToolProvider, self).is_valid_request(validator):
            raise InvalidLTIRequestError()
        return True


