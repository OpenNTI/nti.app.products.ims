#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import component

from zope import interface

from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectModifiedEvent

from nti.ims.lti.interfaces import IConfiguredTool, IResourceSelectionTool, ILinkSelectionTool, IAssignmentSelectionTool
from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

SUPPORTED_LMS = ('nextthought.com',
                 'canvas.instructure.com',)

EXTENSION_KEYS = {'resource': 'resource_selection',
                  'link': 'link_selection',
                  'migration': 'migration_selection',
                  'assignment': 'assignment_selection',
                  'homework': 'homework_selection',
                  'editor': 'editor_button'}


def _get_lms_extensions(config):
    for lms in SUPPORTED_LMS:
        if config.get_ext_params(lms) is not None:
            return lms


@component.adapter(IConfiguredTool, IObjectModifiedEvent)
@component.adapter(IConfiguredTool, IObjectAddedEvent)
def register_content_selection(tool, _event):
    config = tool.config
    lms = _get_lms_extensions(config)
    if lms is not None:
        if config.get_ext_param(lms, EXTENSION_KEYS['link']):  # Prefer Deep Linking if we have the option
            param = config.get_ext_param(lms, EXTENSION_KEYS['link'])
            tool.selection_height = param.get('selection_height')
            tool.selection_width = param.get('selection_width')
            interface.alsoProvides(tool, ILinkSelectionTool)
        elif config.get_ext_param(lms, EXTENSION_KEYS['resource']):  # Canvas ExternalToolLinkSelection spec
            param = config.get_ext_param(lms, EXTENSION_KEYS['resource'])
            tool.selection_height = param.get('selection_height')
            tool.selection_width = param.get('selection_width')
            interface.alsoProvides(tool, IResourceSelectionTool)
        else:
            interface.noLongerProvides(tool, IResourceSelectionTool)
            interface.noLongerProvides(tool, ILinkSelectionTool)


@component.adapter(IConfiguredTool, IObjectModifiedEvent)
@component.adapter(IConfiguredTool, IObjectAddedEvent)
def register_assignment_selection(tool, _event):
    config = tool.config
    lms = _get_lms_extensions(config)
    if lms is not None:
        if config.get_ext_param(lms, EXTENSION_KEYS['assignment']):
            param = config.get_ext_param(lms, EXTENSION_KEYS['assignment'])
            tool.message_type = 'ContentItemSelectionRequest'
            tool.text = param.get('text')
            tool.url = param.get('url')
            interface.alsoProvides(tool, IAssignmentSelectionTool)
        else:
            interface.noLongerProvides(tool, IAssignmentSelectionTool)
