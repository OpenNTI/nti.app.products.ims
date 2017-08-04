#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from z3c.table import column
from z3c.table import table

from zope.publisher.interfaces.browser import IBrowserRequest

from nti.app.authentication import get_remote_user

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization_acl import has_permission

from nti.externalization.oids import to_external_ntiid_oid


class LTIToolsTable(table.Table):

    batchSize = 25
    startBatchingAt = 25
    sortOn = None

    def batchRows(self):
        try:
            super(LTIToolsTable, self).batchRows()
        except IndexError:
            self.batchStart = len(self.rows) - self.getBatchSize()
            super(LTIToolsTable, self).batchRows()


class TitleColumn(column.Column):
    weight = 1
    header = u'Title'

    def renderCell(self, tool):
        return tool.title


class DescriptionColumn(column.Column):
    weight = 2
    header = u'Description'

    def renderCell(self, tool):
        return tool.description


class KeyColumn(column.Column):
    weight = 3
    header = u'Consumer Key'

    def renderCell(self, tool):
        return tool.consumer_key


class SecretColumn(column.Column):
    weight = 4
    header = u'Secret'

    def renderCell(self, tool):
        return tool.secret


class DeleteColumn(column.Column):
    weight = 6
    buttonTitle = 'DELETE'

    def renderCell(self, item):

        action_url = self.request.resource_url(item, '@@delete')
        return """<button onclick=deleteTool('%s')>%s</button>""" \
               % (action_url, self.buttonTitle)


class EditColumn(column.Column):
    weight = 5
    buttonTitle = 'EDIT'

    def renderCell(self, item):

        action_url = self.request.resource_url(item, '@@edit_view')
        return """<form action='%s'>
                    <button type='submit'>%s</button>
                  </form>
               """ \
               % (action_url, self.buttonTitle)


class ToolConfigColumn(column.Column):
    weight = 7
    buttonTitle = 'Tool Config'

    def renderCell(self, item):

        action_url = self.request.resource_url(item, '@@tool_config_view')
        return """<form action='%s'>
                    <button type='submit'>%s</button>
                  </form>
               """ \
               % (action_url, self.buttonTitle)

def make_specific_table(tableClassName, container, request):

    the_table = tableClassName(container, IBrowserRequest(request))

    try:
        the_table.update()
    except IndexError:
        the_table.batchStart = len(the_table.rows) - the_table.getBatchSize()
        the_table.update()

    return the_table

