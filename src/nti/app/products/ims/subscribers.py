#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope import interface

from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectModifiedEvent

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

DECORATOR_IFACES = (('link_selection', IDeepLinking),
                    ('resource_selection', IExternalToolLinkSelection),)

logger = __import__('logging').getLogger(__name__)


def extension_ifaces(tool, _event):
    for (key, iface) in DECORATOR_IFACES:
        params = tool.config.get_ext_param('canvas.instructure.com',
                                           key)
        if params:
            interface.alsoProvides(tool, iface)
        elif iface.providedBy(tool):
            interface.noLongerProvides(tool, iface)


@component.adapter(IConfiguredTool, IObjectModifiedEvent)
def tool_modified_event(tool, event):
    extension_ifaces(tool, event)


@component.adapter(IConfiguredTool, IObjectAddedEvent)
def tool_added_event(tool, event):
    extension_ifaces(tool, event)
