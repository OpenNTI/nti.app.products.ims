#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.ims.lti.interfaces import IToolConfigBuilder

CONSUMER_EXT_KEY = 'canvas.instructure.com'

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IToolConfigBuilder)
class OAuthComplianceFieldConfigBuilder(object):

    def __init__(self, tool):
        pass

    def configure(self, config):
        canvas_ext = {
            'oauth_compliant': 'true',
            'privacy_level': 'Public'
        }
        config.set_ext_params(CONSUMER_EXT_KEY, canvas_ext)
        return config
