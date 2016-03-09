#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.internalization import read_body_as_external_object
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims.views import LTIPathAdapter

from nti.common.maps import CaseInsensitiveDict

#from nti.externalization.interfaces import LocatedExternalDict

response_message = """
<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeResponse xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
   <imsx_POXHeader>
      <imsx_POXResponseHeaderInfo>
         <imsx_version>V1.0</imsx_version>
         <imsx_messageIdentifier>4560</imsx_messageIdentifier>
         <imsx_statusInfo>
            <imsx_codeMajor>success</imsx_codeMajor>
            <imsx_severity>status</imsx_severity>
            <imsx_description>Score for 3124567 is now 0.92</imsx_description>
            <imsx_messageRefIdentifier>999999123</imsx_messageRefIdentifier>
            <imsx_operationRefIdentifier>replaceResult</imsx_operationRefIdentifier>
         </imsx_statusInfo>
      </imsx_POXResponseHeaderInfo>
   </imsx_POXHeader>
   <imsx_POXBody>
      <replaceResultResponse />
   </imsx_POXBody>
</imsx_POXEnvelopeResponse>
"""
@view_config(name='Grade')
@view_config(name='grade')
@view_defaults(route_name='objects.generic.traversal',
			   renderer='rest',
			   context=LTIPathAdapter)
class LTIGradeView(AbstractAuthenticatedView,
				   ModeledContentUploadRequestUtilsMixin):

	def readInput(self, value=None):
		if self.request.body:  # It's a post request
			values = read_body_as_external_object(self.request)
		else:
			values = self.request.params  # It's a get request
		result = CaseInsensitiveDict(values)
		return result

	def __call__(self):
		values = self.readInput()
		print(values)
		response = self.request.response
		response.content_type = b'text/xml'
		response.text =response_message
		return response
