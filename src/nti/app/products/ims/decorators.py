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

from nti.app.products.ims import SUPPORTED_LTI_EXTENSIONS

from nti.app.renderers.decorators import AbstractRequestAwareDecorator
from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.externalization.interfaces import IExternalMappingDecorator
from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.interfaces import IConfiguredTool

from nti.links import Link

LINKS = StandardExternalFields.LINKS

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


@component.adapter(IConfiguredTool)
@interface.implementer(IExternalMappingDecorator)
class ContentSelectionLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _do_decorate_external(self, context, result):
        for (rel, iface, element) in SUPPORTED_LTI_EXTENSIONS:
            if iface.providedBy(context):
                _links = result.setdefault(LINKS, [])
                _links.append(
                    Link(context, rel=CONTENT_SELECTION, elements=(element,))
                )
