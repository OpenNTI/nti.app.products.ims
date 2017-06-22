#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

#: IMS Path
IMS = u'IMS'

#: LTI Path
LTI = u'LTI'

#: SIS Path
SIS = u'SIS'

#: Tools Path
TOOLS = u'TOOLS'
