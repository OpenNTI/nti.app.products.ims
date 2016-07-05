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

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims.views import LTIPathAdapter

from nti.common.maps import CaseInsensitiveDict

from nti.externalization.interfaces import IExternalRepresentationReader

from nti.ims.lti.oauth_service import validate_request

from nti.ims.lti.tool_provider import ToolProvider

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

text_message = "Hello dunia"


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
		response.content_type = b'text/plain'
		response.text = text_message
		val_req = validate_request(values)
		if (val_req):
			provider = ToolProvider("key", "secret", values)
			lis_outcome_service_url = values['lis_outcome_service_url'][0]
			req = sign_request(lis_outcome_service_url, 'key', 'secret', method='post')
		return response

def sign_request(url, key, secret, method='get'):
	auth = OAuth1(key, client_secret=secret)
	oauth_parameters = get_oauth_parameters(key, None)
	url_parameters = {}
	
	#TODO : generate correct oauth signature (apparently moodle said 'Message signature not valid', but yes it now recoqnizes the consumer key)
	#check this link https://github.com/kelsmj/twitter_signature/blob/master/twitter_sign.py for references.
	#the code in github has error (line 226)  >> character mapping must return integer, None or unicode <<
	#yet it is already modified here so we won't get that error (line 226)
	#we need to move this method and others once we figure out the correct oauth signature.. this is only for the sake of easy debugging
	oauth_parameters['oauth_signature'] = generate_signature(
											method, 
											url, 
											url_parameters, 
											oauth_parameters,
											key, 
											secret,
											oauth_token_secret=None, 
											status=None)

	#making a request to send the grade
	headers = {'Content-Type': "application/xml", 'Authorization' : create_auth_header(oauth_parameters)}
	req = requests.post(url, data=grade, headers = headers)
	print (req.status_code)
	return req

def get_oauth_parameters(consumer_key, access_token):
    """Returns OAuth parameters needed for making request"""
    oauth_parameters = {
        'oauth_timestamp': str(int(time.time())),
        'oauth_signature_method': "HMAC-SHA1",
        'oauth_version': "1.0",
        'oauth_nonce': get_nonce(),
        'oauth_consumer_key': consumer_key,
        'oauth_callback' : 'about:blank'
    }
    return oauth_parameters


def escape(s):
    """Percent Encode the passed in string"""
    return urllib.quote(s, safe='~')


def get_nonce():
    """Unique token generated for each request"""
    n = base64.b64encode(
        ''.join([str(random.randint(0, 9)) for i in range(24)]))
    return n


def generate_signature(method, url, url_parameters, oauth_parameters,
                       oauth_consumer_key, oauth_consumer_secret,
                       oauth_token_secret=None, status=None):
    """Create the signature base string"""

    #Combine parameters into one hash
    temp = collect_parameters(oauth_parameters, status, url_parameters)

    #Create string of combined url and oauth parameters
    parameter_string = stringify_parameters(temp)

    #Create your Signature Base String
    signature_base_string = (
        method.upper() + '&' +
        escape(str(url)) + '&' +
        escape(parameter_string)
    )

    #Get the signing key
    signing_key = create_signing_key(oauth_consumer_secret, oauth_token_secret)

    return calculate_signature(signing_key, signature_base_string)

def collect_parameters(oauth_parameters, status, url_parameters):
    """Combines oauth, url and status parameters"""
    #Add the oauth_parameters to temp hash
    temp = oauth_parameters.copy()

    #Add the status, if passed in.  Used for posting a new tweet
    if status is not None:
        temp['status'] = status

    #Add the url_parameters to the temp hash
    for k, v in url_parameters.iteritems():
        temp[k] = v

    return temp


def calculate_signature(signing_key, signature_base_string):
    """Calculate the signature using SHA1"""
    signing_key = str(signing_key)
    signature_base_string = str(signature_base_string)
    hashed = hmac.new(signing_key, signature_base_string, hashlib.sha1)

    sig = binascii.b2a_base64(hashed.digest())[:-1]

    return escape(sig)


def create_signing_key(oauth_consumer_secret, oauth_token_secret=None):
    """Create key to sign request with"""
    signing_key = escape(oauth_consumer_secret) + '&'

    if oauth_token_secret is not None:
        signing_key += escape(oauth_token_secret)

    return signing_key


def create_auth_header(parameters):
    """For all collected parameters, order them and create auth header"""
    ordered_parameters = {}
    ordered_parameters = collections.OrderedDict(sorted(parameters.items()))
    auth_header = (
        '%s="%s"' % (k, v) for k, v in ordered_parameters.iteritems())
    val = "OAuth " + ', '.join(auth_header)
    return val


def stringify_parameters(parameters):
    """Orders parameters, and generates string representation of parameters"""
    output = ''
    ordered_parameters = {}
    ordered_parameters = collections.OrderedDict(sorted(parameters.items()))

    counter = 1
    for k, v in ordered_parameters.iteritems():
        output += escape(str(k)) + '=' + escape(str(v))
        if counter < len(ordered_parameters):
            output += '&'
            counter += 1

    return output



