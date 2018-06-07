#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from nti.externalization.internalization import update_from_external_object
from zope.schema._bootstrapinterfaces import RequiredMissing
from zope.schema.interfaces import WrongContainedType

__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length, is_
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
    'launch_url': u'http://www.test_url.com',
    'secure_launch_url': u'https://www.secure_test_url.com'
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

        tools.delete_tool(tool)
        assert_that(tools, has_length(0))

        tool = ConfiguredTool(**KWARGS)
        tool.config = config
        tools.add_tool(tool)
        assert_that(tools, has_length(1))
        tools.delete_tool(tool.ntiid)
        assert_that(tools, has_length(0))

    def test_error_handling(self):
        # Configured Tool properly creates
        tool = ConfiguredTool()
        config = PersistentToolConfig(**KWARGS)
        ext_tool = {u'MimeType': u'application/vnd.nextthought.ims.consumer.configuredtool',
                    u'config': config,
                    u'secret': u'test_secret',
                    u'consumer_key': u'test_consumer'}

        update_from_external_object(containedObject=tool, externalObject=ext_tool)

        # Null values config
        tool = ConfiguredTool()
        config = PersistentToolConfig()
        ext_tool[u'config'] = config
        with self.assertRaises(WrongContainedType) as context:
            update_from_external_object(containedObject=tool, externalObject=ext_tool)
        assert_that(str(context.exception), is_("([RequiredMissing('launch_url'),"
                                                " RequiredMissing('secure_launch_url'),"
                                                " RequiredMissing('description'),"
                                                " RequiredMissing('title')],"
                                                " 'config')"))

        # Malformed URL config
        tool = ConfiguredTool()
        bad_config = {u'title': 'test',
                      u'description': 'test description',
                      u'launch_url': 'test.com',
                      u'secure_launch_url': 'test.com'}
        config = PersistentToolConfig(**bad_config)
        ext_tool[u'config'] = config
        with self.assertRaises(WrongContainedType) as context:
            update_from_external_object(containedObject=tool, externalObject=ext_tool)
        assert_that(str(context.exception), is_("([InvalidURI('test.com',"
                                                " u'The specified URL is not valid.', 'launch_url'),"
                                                " InvalidURI('test.com', u'The specified URL is not valid.',"
                                                " 'secure_launch_url')], 'config')"))
