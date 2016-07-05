#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
from urlparse import parse_qs
import requests

from zope import component

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims.views import LTIPathAdapter

from nti.common.maps import CaseInsensitiveDict

from nti.externalization.interfaces import IExternalRepresentationReader

from nti.ims.lti.oauth_service import validate_request

from nti.ims.lti.tool_provider import ToolProvider
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth1Session

response_message = """
<html>
<body>
<p> Hello World! </p>
</body>
</html>
"""
grade = """
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

	def _handle_unicode(self, value, request):
		if isinstance(value, unicode):  # already unicode
			return value
		try:
			value = unicode(value, request.charset)
		except UnicodeError:
			# Try the most common web encoding
			value = unicode(value, 'iso-8859-1')
		return value

	def read_input_data(self, request, ext_format='json'):
		reader = component.getUtility(IExternalRepresentationReader, name=ext_format)
		value = self._handle_unicode(request.body, request)
		__traceback_info__ = value
		try:
			result = reader.load(value)
		except Exception:  # not json
			result = value
		return result

	def readInput(self, value=None):
		if self.request.body:  # It's a post request
			values = self.read_input_data(self.request)
			if isinstance(values, six.string_types):
				values = parse_qs(values)
		else:
			values = self.request.params  # It's a get request
		result = CaseInsensitiveDict(values)
		return result

	def __call__(self):
		from IPython.core.debugger import Tracer; Tracer()()
		values = self.readInput()
		response = self.request.response
		response.content_type = b'text/html'
		response.text = response_message
		val_req = validate_request(values)
		if (val_req):
			# then check for the lis_outcome_url to send back grade data
			# launch_mix = LaunchParamsMixin()
			provider = ToolProvider("key", "secret", values)
			#if (provider.is_outcome_service()):
			#	provider.post_read_result({})
			print ("posted")
			post_to = values['lis_outcome_service_url'][0]
			auth = OAuth1('key', client_secret='secret', signature_type='auth_header')
			#making a request to send the grade
			headers = {'Content-Type': "application/xml",
		        'Authorization': "OAuth %s" % auth, 'oauth_consumer_key':'key'}
			req = requests.post(post_to, data=grade,
				headers = headers)
			print (req.status_code)
		return response
