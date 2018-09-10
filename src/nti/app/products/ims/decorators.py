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

from nti.app.products.ims import CONTENT_SELECTION

from nti.app.renderers.decorators import AbstractRequestAwareDecorator
from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.externalization.interfaces import IExternalMappingDecorator
from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

from nti.links import Link

LINKS = StandardExternalFields.LINKS

DEEP_LINKING_PATH = '@@deep_linking'

EXTERNAL_TOOL_LINK_SELECTION_PATH = '@@external_tool_link_selection'

logger = __import__('logging').getLogger(__name__)


@component.adapter(IConfiguredTool)
@interface.implementer(IExternalMappingDecorator)
class ConfiguredToolEditLinkDecorator(EditLinkDecorator):

    def _has_permission(self, context):
        return has_permission(nauth.ACT_UPDATE, context, self.request)


@component.adapter(IConfiguredTool)
@interface.implementer(IExternalMappingDecorator)
class ConfiguredToolDeletedDecorator(AbstractRequestAwareDecorator):

    def _do_decorate_external(self, context, result):
        result['deleted'] = IDeletedObjectPlaceholder.providedBy(context)


# Register additional urls here for decorating assignment_selection etc

LTI_EXTENSION_URLS = ((IDeepLinking, DEEP_LINKING_PATH),
                      (IExternalToolLinkSelection, EXTERNAL_TOOL_LINK_SELECTION_PATH),)


@component.adapter(IConfiguredTool)
@interface.implementer(IExternalMappingDecorator)
class ContentSelectionLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _do_decorate_external(self, context, result):
        for iface, element in LTI_EXTENSION_URLS:
            if iface.providedBy(context):
                _links = result.setdefault(LINKS, [])
                _links.append(
                    Link(context, rel=CONTENT_SELECTION, elements=(element,))
                )
