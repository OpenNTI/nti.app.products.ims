#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from random import randint
import ConfigParser
import urllib
import random
import base64
import hmac
import binascii
import time
import collections
import hashlib
import json

from requests_oauthlib import OAuth1, OAuth1Session


import six
from urlparse import parse_qs
import requests

from zope import component
import zope.formlib.form

from zope import interface
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher import interfaces

from zc.intid import IIntIds

from z3c.table import table
from z3c.table import column
from z3c.table import batch

from pyramid import httpexceptions  as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims.views import LTIPathAdapter

from nti.common.maps import CaseInsensitiveDict

from nti.externalization.interfaces import IExternalRepresentationReader

from nti.ims.lti.oauth_service import validate_request

from nti.ims.lti.tool_provider import ToolProvider
from nti.dataserver.users import interfaces as user_interfaces
from nti.dataserver import interfaces as nti_interfaces
from pprint import pprint
from persistent import Persistent
import zope.interface
from zope.interface import implements
from zope.app.container.contained import Contained
from zope.formlib import form
from zope import interface, schema
from zope.schema.fieldproperty import FieldProperty
import os
from zope.publisher.browser import TestRequest
from zope.browserpage import ViewPageTemplateFile

from zope.publisher.interfaces.browser import IBrowserRequest
from pyramid.renderers import render_to_response

response_message = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
	  xmlns:tal="http://xml.zope.org/namespaces/tal">
	<head>
		<meta http-equiv="content-type" content="text/html; charset=utf-8" />
		<title>Addition Quiz</title>
		
	</head>
	<body class="normal-text">
		<form id='userform'method='post' action="">
	  		Addition Quiz<br>
	  		Find the sum: 10 + 15 <br>
	  		<input type="number" name="answer" value=""><br>
	  		<input type="submit" value="Submit">
		</form>	
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

#Global provider object to generate outcome service for grades on Moddle.
# This will need to be handled differently in the future, but since there's
# only one view we need it to keep the provider from getting erased upon the 
# submission of an answer to the addition question. 
provider = None


@view_config(name='Grade')
@view_config(name='grade')
@view_defaults(route_name='objects.generic.traversal',
			   renderer='rest',
			   context=LTIPathAdapter)
@view_config( request_method='GET')
class LTIGradeView(ModeledContentUploadRequestUtilsMixin):
	def __init__(self, request):
    		self.request = request
	
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

		if(values.get('answer')): #user has submitted quiz
			if(values['answer'][0] == '25'):
				outcome = provider.generate_outcome_request_xml(score=1)
				response.text = "<html><p> Correct!</p>" + "<textarea>" + outcome + "</textarea>" + "</html>" 
				#add code to send grade from tool_provider and outcome_service
				#grade for correct answer is 1
				#note that we'll need to find a way to store the provider from a previous request
				#maybe we should use a global variable or send the values back and forth with the form
				#submission.
				#next step is to just print out the XML required for the grading system.
				
			else:
				outcome = provider.generate_outcome_request_xml(score=0)
				response.text = "<html><p> Incorrect.</p>" + "<textarea>" + outcome + "</textarea>" + "</html>" 
				#add grade for incorrect, 0.
				
			post_to = provider.params['lis_outcome_service_url'][0]
			auth = OAuth1('key', client_secret='secret', signature_type='auth_header')
			#making a request to send the grade back to Moodle
			headers = {'Content-Type': "application/xml"}
			req = requests.post(post_to, data=grade,
					headers = headers, auth=auth)
		elif (values.get('oauth_consumer_key')): #need to validate user
			val_req = validate_request(values)
			if (val_req):
				global provider
				provider = ToolProvider("key", "secret", values)
				response.text = response_message
		return response