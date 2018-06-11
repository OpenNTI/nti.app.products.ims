#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import interface

from nti.app.products.ims.interfaces import IConfiguredToolExtensionsBuilder

from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


def _do_deep_linking(params):
    return params['resource_selection'].get('message_type') == 'ContentItemSelectionRequest'


class ConfiguredToolExtensions(object):

    def __init__(self, tool, config):
        self.tool = tool
        self.config = config
        self.params = config.get_ext_params('canvas.instructure.com')
        if self.params is None:
            self.params = {}


@interface.implementer(IConfiguredToolExtensionsBuilder)
class DeepLinking(ConfiguredToolExtensions):

    def build_extensions(self):
        if 'resource_selection' in self.params and _do_deep_linking(self.params):
            interface.alsoProvides(self.tool, IDeepLinking)


class ExternalToolLinkSelection(ConfiguredToolExtensions):

    def build_extensions(self):
        if 'resource_selection' in self.params and not _do_deep_linking(self.params):
            interface.alsoProvides(self.tool, IExternalToolLinkSelection)
