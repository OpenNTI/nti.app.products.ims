#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from zope import component
from zope import interface

from nti.app.products.ims import CONTENT_SELECTION

from nti.app.renderers.decorators import AbstractRequestAwareDecorator
from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

from nti.links import Link

LINKS = StandardExternalFields.LINKS

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

DEEP_LINKING_PATH = '@@deep_linking'

EXTERNAL_TOOL_LINK_SELECTION_PATH = '@@external_tool_link_selection'


@component.adapter(IConfiguredTool)
@interface.implementer(IExternalObjectDecorator)
class ConfiguredToolEditLinkDecorator(EditLinkDecorator):

    def _has_permission(self, context):
        return has_permission(nauth.ACT_UPDATE, context, self.request)


@component.adapter(IConfiguredTool)
@interface.implementer(IExternalObjectDecorator)
class ConfiguredToolDeletedDecorator(AbstractRequestAwareDecorator):

    def _do_decorate_external(self, context, result):
        result['deleted'] = IDeletedObjectPlaceholder.providedBy(context)


CONTENT_SELECTION_URLS = ((IDeepLinking, DEEP_LINKING_PATH),
                          (IExternalToolLinkSelection, EXTERNAL_TOOL_LINK_SELECTION_PATH),)

@component.adapter(IConfiguredTool)
@interface.implementer(IExternalObjectDecorator)
class ContentSelectionLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _do_decorate_external(self, context, result):
        for iface, element in CONTENT_SELECTION_URLS:
            if iface.providedBy(context):
                _links = result.setdefault(LINKS, [])
                _links.append(Link(context, rel=CONTENT_SELECTION, elements=(element,)))
                return
