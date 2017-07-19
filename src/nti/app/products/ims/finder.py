#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lti import InvalidLTIRequestError

from zope.component import queryAdapter

from nti.app.products.ims import MessageFactory as _

from nti.app.products.ims.interfaces import ILTIUserFactory

LAUNCH_PARAM_FIELDS = [
    'tool_consumer_instance_guid',
    'tool_consumer_instance_url',
    'tool_consumer_instance_name',
    'oauth_consumer_key',
    'tool_consumer_info_product_family_code'
]


class LTIUserFactoryFinder(object):

    def __init__(self, request):
        self.adapter = None
        # Check the suspected locations
        for field in LAUNCH_PARAM_FIELDS:
            try:
                adapter_name = request.params[field]
                adapter = queryAdapter(request, 
                                       ILTIUserFactory, 
                                       name=adapter_name)
                if adapter:
                    self.adapter = adapter
                    break
            except KeyError:
                logger.exception('No key in field %s', field)
        if not self.adapter:
            msg = _('No adapter was found for this consumer tool')
            raise InvalidLTIRequestError(msg)

    def user_for_request(self, request=None):
        return self.adapter.user_for_request(request)
