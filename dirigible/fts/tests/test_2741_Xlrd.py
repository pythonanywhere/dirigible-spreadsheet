# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2741_Xlrd(FunctionalTest):

    def test_can_use_xlrd(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # He imports xlrd
        self.prepend_usercode("import xlrd")
        self.append_usercode("worksheet.A1.value = 4")

        # * and it works
        self.wait_for_cell_value(1, 1, '4')

