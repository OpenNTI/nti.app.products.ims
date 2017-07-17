#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.component import queryAdapter

from nti.app.products.ims.interfaces import ISessionProvider
from nti.app.products.ims.interfaces import IToolConsumerSpecialParams

SITE_ADAPTER_FIELDS = [
    'tool_consumer_instance_guid',
    'tool_consumer_instance_name',
    'tool_consumer_instance_description',
    'tool_consumer_instance_url'
]

TOOL_CONSUMER_ADAPTER_FIELDS = [
    'tool_consumer_family_code',
    'consumer_key'
]


class SessionProviderFinder(object):

    def find(self, request):

        # Check the suspected locations
        for field in SITE_ADAPTER_FIELDS:
            adapter = queryAdapter(request, ISessionProvider, name=field)
            if adapter:
                return adapter

        # Make sure there isn't any special condition if we couldn't find an adapter
        for field in TOOL_CONSUMER_ADAPTER_FIELDS:
            adapter = queryAdapter(request, IToolConsumerSpecialParams, name=field)
            if adapter:
                return adapter
        return None
