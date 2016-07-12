#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


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

class IPerson(interface.Interface):
 
      id = schema.TextLine(
          title=u'ID',
          readonly=True,
          required=True)
 
      name = schema.TextLine(
          title=u'Name',
          required=True)
 
      gender = schema.Choice(
          title=u'Gender',
          values=('male', 'female'),
          required=False)
 
      age = schema.Int(
          title=u'Age',
          description=u"The person's age.",
          min=0,
          default=20,
          required=False)
 
      @interface.invariant
      def ensureIdAndNameNotEqual(person):
          if person.id == person.name:
              raise interface.Invalid(
                  "The id and name cannot be the same.")

class Person(object):

    interface.implements(IPerson)
    id = FieldProperty(IPerson['id'])
    name = FieldProperty(IPerson['name'])
    gender = FieldProperty(IPerson['gender'])
    age = FieldProperty(IPerson['age'])
 
    def __init__(self, id, name, gender=None, age=None):
        self.id = id
        self.name = name
        if gender:
            self.gender = gender
        if age:
            self.age = age
 
    def __repr__(self):
      	return '<%s %r>' % (self.__class__.__name__, self.name)

class PersonAddForm(form.AddForm):
 
      fields = form.Fields(IPerson)
 
      def create(self, data):
          return Person(**data)
 
      def add(self, object):
          self.context[object.id] = object
 
      def nextURL(self):
          return 'index.html'

def addTemplate(form):
      form.template = ViewPageTemplateFile.bind_template(
          ViewPageTemplateFile.ViewPageTemplateFile(
              'simple_edit.pt', os.path.dirname(tests.__file__)), form)

@view_config(name='Grade')
@view_config(name='grade')
@view_defaults(route_name='objects.generic.traversal',
			   renderer='rest',
			   context=LTIPathAdapter)
@view_config( route_name='objects.generic.traversal',
			  renderer='account_profile_view.pt',
			  request_method='GET')
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
			
			"""
			print ("posted")
			"""
			post_to = values['lis_outcome_service_url'][0]
			auth = OAuth1('key', client_secret='secret', signature_type='auth_header')
			#making a request to send the grade
			headers = {'Content-Type': "application/xml"}
			req = requests.post(post_to, data=grade,
				headers = headers, auth=auth)
			#print (req.status_code)
			request = self.request
			addForm = PersonAddForm(None, request)
			fields = form.Fields(IPerson)
			#interfaces.IFieldsForm.providedBy(addForm)
			#addForm.update()
			context = post_to
			widgets = zope.formlib.form.setUpWidgets( fields, 'form', request.context,
													  IBrowserRequest( request),
													  # Without this, it needs request.form
													  ignore_request=True )

			return widgets