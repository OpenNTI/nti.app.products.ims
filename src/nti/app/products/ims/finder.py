#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lti import InvalidLTIRequestError

from nti.app.products.ims import MessageFactory as _

from nti.app.products.ims.interfaces import ILTIUserFactory

from nti.ims.lti.utils import LaunchRequestFilter

LAUNCH_PARAM_FIELDS = [
    'tool_consumer_instance_guid',
    'tool_consumer_instance_url',
    'tool_consumer_instance_name',
    'oauth_consumer_key',
    'tool_consumer_info_product_family_code'
]


class LTIUserFactoryFinder(object):

    def __init__(self, request):

        self.adapter = LaunchRequestFilter.filter_for_adapter(request,
                                                              ILTIUserFactory)
        if not self.adapter:
            msg = _('No adapter was found for this consumer tool')
            raise InvalidLTIRequestError(msg)

    def user_for_request(self, request=None):
        return self.adapter.user_for_request(request)
