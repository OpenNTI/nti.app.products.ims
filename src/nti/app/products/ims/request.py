from __future__ import print_function, absolute_import, division


__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.app.products.ims.interfaces import IRequest


@interface.implementer(IRequest)
class Request(object):

    def __init__(self, request):
        self.source = request.consumer_key