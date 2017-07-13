from __future__ import print_function, absolute_import, division



__docformat__ = "restructuredtext en"


from zope import interface
from zope import component

from pyramid import httpexceptions as hexc

from nti.app.products.ims.interfaces import ISessionFactory
from nti.appserver.interfaces import IApplicationSettings


def _web_root():
    settings = component.getUtility(IApplicationSettings)
    web_root = settings.get('web_app_root', '/NextThoughtWebApp/')
    return web_root


@interface.implementer(ISessionFactory)
class SISSession(object):

    def begin_session(self, request):
        return hexc.HTTPSeeOther(location=_web_root())

@interface.implementer(ISessionFactory)
class JanuxSession(object):
    pass