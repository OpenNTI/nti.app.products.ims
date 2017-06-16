#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from .interfaces import ILTIRequest

@interface.implementer(ILTIRequest)
class PyramidLTIRequest(object):

    def __init__(self, pyramid_request):
        self.params = dict(pyramid_request.params)
        self.url = pyramid_request.url.rsplit('?', 1)[0]
        self.headers = pyramid_request.headers
