#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.app.products.ims.interfaces import ILTIRequest


@interface.implementer(ILTIRequest)
class PyramidLTIRequest(object):

    def __init__(self, request):
        self.headers = request.headers
        self.params = dict(request.params)
        self.url = request.url.rsplit('?', 1)[0]