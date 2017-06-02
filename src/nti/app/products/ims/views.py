#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.location.interfaces import IContained

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.ims import IMS
from nti.app.products.ims import LTI
from nti.app.products.ims import SIS


@interface.implementer(IPathAdapter, IContained)
class IMSPathAdapter(object):

    __name__ = IMS

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context

    def __getitem__(self, key):
        if key == LTI:
            return LTIPathAdapter(self, self.request)
        elif key == SIS:
            return SISPathAdapter(self, self.request)
        raise KeyError(key)


@interface.implementer(IPathAdapter, IContained)
class LTIPathAdapter(object):

    __name__ = LTI

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent


@interface.implementer(IPathAdapter, IContained)
class SISPathAdapter(object):

    __name__ = SIS

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent
