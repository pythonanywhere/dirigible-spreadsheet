# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#
from textwrap import dedent

from functionaltest import FunctionalTest


class test_2603_WorksheetsMayOnlyContainCells(FunctionalTest):

    def test_setting_worksheet_location_to_non_cell_raises(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters usercode which sets a worksheet location to a non-cell
        self.append_usercode('worksheet[1,1] = 123')
        error_line = len(self.get_usercode().split('\n'))
        expected = dedent('''
            TypeError: Worksheet locations must be Cell objects
                User code line %d''' % (error_line,))[1:]
        self.wait_for_console_content(expected)

        # hooray!

