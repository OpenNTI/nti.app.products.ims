#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.app.products.ims.interfaces import ILTIRequest

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ILTIRequest)
class PyramidLTIRequest(object):

    def __init__(self, request):
        self.headers = request.headers
        self.params = dict(request.params)
        self.url = request.url.rsplit('?', 1)[0]
