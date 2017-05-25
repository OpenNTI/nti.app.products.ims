#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.container.contained import Contained

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.ims import IMS
from nti.app.products.ims import LTI
from nti.app.products.ims import SIS


@interface.implementer(IPathAdapter)
class IMSPathAdapter(Contained):

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


@interface.implementer(IPathAdapter)
class LTIPathAdapter(Contained):

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent
        self.__name__ = LTI


@interface.implementer(IPathAdapter)
class SISPathAdapter(Contained):

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent
        self.__name__ = SIS
