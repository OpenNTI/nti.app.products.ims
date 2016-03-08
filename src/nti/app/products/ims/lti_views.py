#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.internalization import read_body_as_external_object
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims.views import LTIPathAdapter

from nti.common.maps import CaseInsensitiveDict

from nti.externalization.interfaces import LocatedExternalDict

@view_config(name='Grade')
@view_config(name='grade')
@view_defaults(route_name='objects.generic.traversal',
			   renderer='rest',
			   context=LTIPathAdapter)
class LTIGradeView(AbstractAuthenticatedView,
				   ModeledContentUploadRequestUtilsMixin):

	def readInput(self, value=None):
		if self.request.body: # It's a post request
			values = read_body_as_external_object(self.request)
		else:
			values = self.request.params # It's a get request
		result = CaseInsensitiveDict(values)
		return result

	def __call__(self):
		values = self.readInput()
		print(values)
		# TODO: do something w/ values
		if False: # results are returned
			result = LocatedExternalDict()
			return result
		else: # otherwise
			return hexc.HTTPOk()
