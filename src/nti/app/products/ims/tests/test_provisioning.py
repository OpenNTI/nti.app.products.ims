#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

from hamcrest import assert_that, is_

from lti import ToolConsumer
from lti import ToolProvider

from zope.component import queryAdapter

from zope import interface

from nti.app.products.ims.interfaces import ISessionProvider
from nti.app.products.ims.interfaces import ILTIRequest

from nti.app.products.ims.tests import SharedConfiguringTestLayer

import nti.testing.base

