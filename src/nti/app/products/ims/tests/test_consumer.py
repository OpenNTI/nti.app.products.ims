#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length
from hamcrest import assert_that

from nti.ims.lti.consumer import ConfiguredTool
from nti.ims.lti.consumer import PersistentToolConfig
from nti.ims.lti.consumer import ConfiguredToolContainer

from nti.app.testing.application_webtest import ApplicationLayerTest


KWARGS = {
    'consumer_key': u'test_key',
    'secret': u'test_secret',
    'title': u'fake_title',
    'description': u'test_desc',
    'launch_url': u'test_url.com',
    'secure_launch_url': u'secure_test_url.com'
}

XML = u"""<xml>
            <title>Test Config</title>
            <description>A Test Config</description>
            <launch_url>http://testconfig.com</launch_url>
            <secure_launch_url>https://testconfig.com</secure_launch_url>
         </xml>
      """


class TestConsumer(ApplicationLayerTest):

    def test_configured_tool_container(self):
        tools = ConfiguredToolContainer()

        config = PersistentToolConfig.create_from_xml(XML)
        tool = ConfiguredTool(**KWARGS)
        tool.config = config
        tools.add_tool(tool)
        assert_that(tools, has_length(1))

        tool = tools[tool]
        assert_that(tools, has_length(1))

        tools.delete_tool(tool)
        assert_that(tools, has_length(0))

        tool = ConfiguredTool(**KWARGS)
        tool.config = config
        tools.add_tool(tool)
        assert_that(tools, has_length(1))
        tools.delete_tool(tool.__name__)
        assert_that(tools, has_length(0))
