#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.ims.lti.interfaces import IToolConfigBuilder


CONSUMER_EXT_KEY = 'canvas.instructure.com'


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
