#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
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

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.internalization import read_body_as_external_object
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.common.maps import CaseInsensitiveDict

from nti.externalization.interfaces import LocatedExternalDict

@view_config(name='LTIGrade')
@view_config(name='lti_grade')
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
		if True: # results are return
			result = LocatedExternalDict()
			return result
		else: # otherwise
			return hexc.HTTPOk()
