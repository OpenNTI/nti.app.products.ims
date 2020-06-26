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
from nti.ims.lti.interfaces import ISelectionRequiredConfiguredTool

from nti.links import FramedLink
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


def _get_selection_dimensions(ext_key, config, default=None):
    ext_params = config.get_ext_param('canvas.instructure.com',
                                      ext_key)
    height = ext_params.get('selection_height', default)
    width = ext_params.get('selection_width', default)
    return height, width


@component.adapter(IConfiguredTool)
@interface.implementer(IExternalMappingDecorator)
class ContentSelectionLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    Decorate rels for specific lti extensions, and a generic rel if content selection
    is required
    """

    def _do_decorate_external(self, context, result):
        for (ext_key, iface, href) in SUPPORTED_LTI_EXTENSIONS:
            if iface.providedBy(context):
                # Change the snake case to camel case ('resource_selection' => 'ResourceSelection')
                rel = ''.join([word.capitalize() for word in ext_key.split('_')])
                _links = result.setdefault(LINKS, [])
                height, width = _get_selection_dimensions(ext_key, context.config, default=500)
                _links.append(
                    FramedLink(context, height=height, width=width, rel=rel, elements=(href,))
                )
        if ISelectionRequiredConfiguredTool.providedBy(context):
            _links = result.setdefault(LINKS, [])
            height = width = 500
            for ext_key in ('resource_selection', 'link_selection'):
                tmp_height, tmp_width = _get_selection_dimensions(ext_key, context.config)
                if tmp_height and tmp_width:
                    width = tmp_width
                    height = tmp_height
                    break
            _links.append(
                FramedLink(context, height=height, width=width,
                           rel='ContentSelection', elements=('@@content_selection',))
            )
