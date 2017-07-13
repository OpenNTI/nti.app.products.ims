"""
Add consumer specific configs here and add them to the IToolConfigBuilder subscribers
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.ims.lti.interfaces import IToolConfigBuilder


@interface.implementer(IToolConfigBuilder)
class CanvasToolConfigBuilder(object):

    def configure(self, config):
        """
        Provides canvas specific customizations
        """
        canvas_ext = {
            'oauth_compliant': 'true',
            'privacy_level': 'Public'
        }
        config.set_ext_params('canvas.instructure.com', canvas_ext)
        return config


