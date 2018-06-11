#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import interface

from nti.app.products.ims.interfaces import IConfiguredToolExtensionsBuilder

from nti.ims.lti.interfaces import IDeepLinking

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class ConfiguredToolExtensions(object):

    def __init__(self, tool, config):
        self.tool = tool
        self.config = config


@interface.implementer(IConfiguredToolExtensionsBuilder)
class DeepLinking(ConfiguredToolExtensions):

    def build_extensions(self):
        if 'resource_selection' in self.config.get_ext_params('nextthought.com'):
            interface.alsoProvides(self.tool, IDeepLinking)
