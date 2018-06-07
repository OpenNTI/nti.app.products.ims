#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from zope import component
from zope import interface

from nti.app.renderers.decorators import AbstractRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.externalization.interfaces import IExternalObjectDecorator

from nti.ims.lti.interfaces import IConfiguredTool

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


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