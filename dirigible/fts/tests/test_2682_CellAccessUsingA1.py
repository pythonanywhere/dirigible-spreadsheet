# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest


class Test_2682_CellAccessUsingA1(FunctionalTest):

    def test_cell_access(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * he uses some convenient ways to find cells in a worksheet object
        self.enter_usercode(dedent('''
            worksheet[1, 2].value = 'a2'
            worksheet["B", 4].value = 'b4'
            worksheet["C6"].value = 'c6'
            worksheet.D8.value = 'd8'
        '''))
        # * which seems to work as he expects
        self.wait_for_cell_value(1, 2, 'a2')
        self.wait_for_cell_value(2, 4, 'b4')
        self.wait_for_cell_value(3, 6, 'c6')
        self.wait_for_cell_value(4, 8, 'd8')

