#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import component

from zope import interface

from zope.lifecycleevent import IObjectModifiedEvent

from nti.app.products.ims.interfaces import IConfiguredTool

from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


def _do_deep_linking(params):
    return params['resource_selection'].get('message_type') == 'ContentItemSelectionRequest'


def _get_params(tool):
    params = tool.config.get_ext_params('canvas.instructure.com')
    if params is None:
        params = {}
    return params


@component.adapter(IConfiguredTool, IObjectModifiedEvent)
def deep_linking(tool, _event):
    params = _get_params(tool)
    if 'resource_selection' in params and _do_deep_linking(params):
        interface.alsoProvides(tool, IDeepLinking)
    elif IDeepLinking.providedBy(tool):
        interface.noLongerProvides(tool, IDeepLinking)


@component.adapter(IConfiguredTool, IObjectModifiedEvent)
def external_tool_link_selection(tool, _event):
    params = _get_params(tool)
    if 'resource_selection' in params and not _do_deep_linking(params):
        interface.alsoProvides(tool, IExternalToolLinkSelection)
    elif IExternalToolLinkSelection.providedBy(tool):
        interface.noLongerProvides(tool, IExternalToolLinkSelection)
