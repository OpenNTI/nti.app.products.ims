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

RESOURCE_SELECTION = (('ContentItemSelectionRequest', IDeepLinking),
                      (None, IExternalToolLinkSelection),)

logger = __import__('logging').getLogger(__name__)


@component.adapter(IConfiguredTool, IObjectModifiedEvent)
@component.adapter(IConfiguredTool, IObjectAddedEvent)
def resource_selection_ifaces(tool, _event):
    params = tool.config.get_ext_param('canvas.instructure.com',
                                       'resource_selection')
    if params is not None:
        resource_selection_type = params.get('message_type', None)
        for message_type, iface in RESOURCE_SELECTION:
            if message_type == resource_selection_type:
                interface.alsoProvides(tool, iface)
            elif iface.providedBy(tool):
                interface.noLongerProvides(tool, iface)
