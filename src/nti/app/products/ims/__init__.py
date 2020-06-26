#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

from nti.ims.lti.interfaces import IAssignmentSelection
from nti.ims.lti.interfaces import IEditorButton
from nti.ims.lti.interfaces import IHomeworkSubmission
from nti.ims.lti.interfaces import ILinkSelection
from nti.ims.lti.interfaces import IMigrationSelection


#: IMS Path
IMS = 'IMS'

#: LTI Path
LTI = 'LTI'

#: SIS Path
SIS = 'SIS'

#: Tools Path
TOOLS = 'TOOLS'

#: A 2-D tuple of supported lti extensions.
#: Index 0 is the extension key in the Tool Config
#: Index 1 is the corresponding interface
#: Index 2 is the decorated href for the appropriate flow
SUPPORTED_LTI_EXTENSIONS = (('link_selection', ILinkSelection, '@@link_selection'),
                            ('resource_selection', ILinkSelection, '@@link_selection'),
                            ('assignment_selection', IAssignmentSelection, '@@assignment_selection'),
                            ('editor_button', IEditorButton, '@@editor_button'),
                            ('homework_submission', IHomeworkSubmission, '@@homework_submission'),
                            ('migration_selection', IMigrationSelection, '@@migration_selection'))
