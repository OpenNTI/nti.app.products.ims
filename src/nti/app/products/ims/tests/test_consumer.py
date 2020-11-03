#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import has_length
from hamcrest import is_
from hamcrest import is_not
from hamcrest import string_contains
does_not = is_not

from zope.event import notify

from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectModifiedEvent

from zope.schema.interfaces import WrongContainedType

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.externalization.internalization import update_from_external_object

from nti.ims.lti.consumer import ConfiguredTool
from nti.ims.lti.consumer import PersistentToolConfig
from nti.ims.lti.consumer import ConfiguredToolContainer

from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides


__docformat__ = "restructuredtext en"

KWARGS = {
    'consumer_key': u'test_key',
    'secret': u'test_secret',
    'title': u'fake_title',
    'description': u'test_desc',
    'launch_url': u'http://www.test_url.com',
    'secure_launch_url': u'https://www.secure_test_url.com'
}

RESOURCE_SELECTION_XML = u"""<xml>
                             <title>Test Config</title>
                             <description>A Test Config</description>
                             <launch_url>http://testconfig.com</launch_url>
                             <secure_launch_url>https://testconfig.com</secure_launch_url>
                             <extensions platform="canvas.instructure.com">
                                <options name="resource_selection">
                                    <property name="enabled">true</property>
                                    <property name="url">https://example.com/chapter_selector</property>
                                    <property name="text">eBook Chapter Selector</property>
                                    <property name="selection_width">500</property>
                                    <property name="selection_height">300</property>
                                </options>
                             </extensions>
                             </xml>"""

DEEP_LINKING_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<cartridge_basiclti_link xmlns="http://www.imsglobal.org/xsd/imslticc_v1p0" xmlns:blti="http://www.imsglobal.org/xsd/imsbasiclti_v1p0" xmlns:lticm="http://www.imsglobal.org/xsd/imslticm_v1p0" xmlns:lticp="http://www.imsglobal.org/xsd/imslticp_v1p0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0p1.xsd http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd">
  <blti:title>TsugiCloud</blti:title>
  <blti:description></blti:description>
  <blti:launch_url>https://www.tsugicloud.org/tsugi/about.php</blti:launch_url>
  <blti:custom>
    <lticm:property name="sub_canvas_account_id">$Canvas.account.id</lticm:property>
    <lticm:property name="sub_canvas_account_name">$Canvas.account.name</lticm:property>
    <lticm:property name="sub_canvas_account_sis_sourceId">$Canvas.account.sisSourceId</lticm:property>
    <lticm:property name="sub_canvas_api_domain">$Canvas.api.domain</lticm:property>
    <lticm:property name="sub_canvas_assignment_id">$Canvas.assignment.id</lticm:property>
    <lticm:property name="sub_canvas_assignment_points_possible">$Canvas.assignment.pointsPossible</lticm:property>
    <lticm:property name="sub_canvas_assignment_title">$Canvas.assignment.title</lticm:property>
    <lticm:property name="sub_canvas_course_id">$Canvas.course.id</lticm:property>
    <lticm:property name="sub_canvas_course_sis_source_id">$Canvas.course.sisSourceId</lticm:property>
    <lticm:property name="sub_canvas_enrollment_enrollment_state">$Canvas.enrollment.enrollmentState</lticm:property>
    <lticm:property name="sub_canvas_membership_concluded_roles">$Canvas.membership.concludedRoles</lticm:property>
    <lticm:property name="sub_canvas_membership_roles">$Canvas.membership.roles</lticm:property>
    <lticm:property name="sub_canvas_root_account.id">$Canvas.root_account.id</lticm:property>
    <lticm:property name="sub_canvas_root_account_sis_source_id">$Canvas.root_account.sisSourceId</lticm:property>
    <lticm:property name="sub_canvas_user_id">$Canvas.user.id</lticm:property>
    <lticm:property name="sub_canvas_user_login_id">$Canvas.user.loginId</lticm:property>
    <lticm:property name="sub_canvas_user_sis_source_id">$Canvas.user.sisSourceId</lticm:property>
    <lticm:property name="sub_canvas_caliper_url">$Caliper.url</lticm:property>
    <lticm:property name="person_address_timezone">$Person.address.timezone</lticm:property>
    <lticm:property name="person_email_primary">$Person.email.primary</lticm:property>
    <lticm:property name="person_name_family">$Person.name.family</lticm:property>
    <lticm:property name="person_name_full">$Person.name.full</lticm:property>
    <lticm:property name="person_name_given">$Person.name.given</lticm:property>
    <lticm:property name="user_image">$User.image</lticm:property>
  </blti:custom>
  <blti:extensions platform="canvas.instructure.com">
     <lticm:property name="privacy_level">public</lticm:property>
<lticm:property name="domain">www.tsugicloud.org</lticm:property>
    <lticm:property name="icon_url">https://www.dr-chuck.net/tsugi-static/img/default-icon-16x16.png</lticm:property>
    <lticm:options name="link_selection">
      <lticm:property name="message_type">ContentItemSelectionRequest</lticm:property>
      <lticm:property name="url">https://www.tsugicloud.org/tsugi/lti/store/index.php?type=link_selection</lticm:property>
    </lticm:options>
    <lticm:options name="assignment_selection">
      <lticm:property name="message_type">ContentItemSelectionRequest</lticm:property>
      <lticm:property name="url">https://www.tsugicloud.org/tsugi/lti/store/index.php?type=assignment_selection</lticm:property>
    </lticm:options>
    <lticm:options name="editor_button">
      <lticm:property name="message_type">ContentItemSelectionRequest</lticm:property>
      <lticm:property name="url">https://www.tsugicloud.org/tsugi/lti/store/index.php?type=editor_button</lticm:property>
    </lticm:options>
    <lticm:property name="text">TsugiCloud</lticm:property>
  </blti:extensions>
</cartridge_basiclti_link>"""


class TestConsumer(ApplicationLayerTest):

    def test_configured_tool_container(self):

        tools = ConfiguredToolContainer()

        config = PersistentToolConfig.create_from_xml(RESOURCE_SELECTION_XML)
        tool = ConfiguredTool(**KWARGS)
        tool.config = config
        tool.ntiid = 'test'
        tools.add_tool(tool)
        assert_that(tools, has_length(1))

        tools.delete_tool(tool)
        assert_that(tools, has_length(0))

        tool = ConfiguredTool(**KWARGS)
        tool.config = config
        tool.ntiid = 'test'
        tools.add_tool(tool)
        assert_that(tools, has_length(1))
        tools.delete_tool(tool.__name__)
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
        assert_that(str(context.exception), string_contains("RequiredMissing('launch_url')",
                                                            "RequiredMissing('title')",
                                                            "config"))

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

    def test_subscribers(self):
        tool = ConfiguredTool()
        config = PersistentToolConfig.create_from_xml(RESOURCE_SELECTION_XML)
        tool.config = config
        notify(ObjectAddedEvent(tool, "Add External Tool Link Selection extension"))
        assert_that(tool, does_not(verifiably_provides(IDeepLinking)))
        assert_that(tool, does_not(validly_provides(IDeepLinking)))
        assert_that(tool, verifiably_provides(IExternalToolLinkSelection))
        assert_that(tool, validly_provides(IExternalToolLinkSelection))

        config = PersistentToolConfig(**KWARGS)
        tool.config = config
        notify(ObjectModifiedEvent(tool, "Remove External Tool Link Selection extension"))
        assert_that(tool, does_not(verifiably_provides(IDeepLinking)))
        assert_that(tool, does_not(validly_provides(IDeepLinking)))
        assert_that(tool, does_not(verifiably_provides(IExternalToolLinkSelection)))
        assert_that(tool, does_not(validly_provides(IExternalToolLinkSelection)))

        config = PersistentToolConfig.create_from_xml(DEEP_LINKING_XML)
        tool.config = config
        notify(ObjectAddedEvent(tool, "Add Deep Linking extension"))
        assert_that(tool, verifiably_provides(IDeepLinking))
        assert_that(tool, validly_provides(IDeepLinking))
        assert_that(tool, does_not(verifiably_provides(IExternalToolLinkSelection)))
        assert_that(tool, does_not(validly_provides(IExternalToolLinkSelection)))
