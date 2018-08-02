#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from z3c.table import table
from z3c.table import column

logger = __import__('logging').getLogger(__name__)


class LTIToolsTable(table.Table):

    batchSize = 25


class TitleColumn(column.Column):
    weight = 1
    header = 'Title'

    def renderCell(self, tool):  # pylint: disable=arguments-differ
        return tool.title


class DeleteColumn(column.Column):
    weight = 3
    buttonTitle = 'DELETE'

    def renderCell(self, item):
        action_url = self.request.resource_url(item)
        return """<button onclick=deleteTool('%s')>%s</button>""" \
               % (action_url, self.buttonTitle)


class EditColumn(column.Column):
    weight = 2
    buttonTitle = 'EDIT'

    def renderCell(self, item):
        action_url = self.request.resource_url(item, '@@edit_view')
        return """<form action='%s'>
                    <button type='submit'>%s</button>
                  </form>
               """ \
               % (action_url, self.buttonTitle)


class ToolConfigColumn(column.Column):
    weight = 4
    buttonTitle = 'Tool Config'

    def renderCell(self, item):
        action_url = self.request.resource_url(item, '@@tool_config_view')
        return """<form action='%s'>
                    <button type='submit'>%s</button>
                  </form>
               """ \
               % (action_url, self.buttonTitle)
