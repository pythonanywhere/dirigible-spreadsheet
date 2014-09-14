# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2762_PythonConversion(FunctionalTest):

    def test_formulas_work_properly(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # the following formula was causing errors
        self.enter_cell_text(1, 1, '10')
        self.enter_cell_text(1, 2, '=[x * A1 for x in range(5)]')
        self.wait_for_cell_value(1, 2, '[0, 10, 20, 30, 40]')

        # as was this one
        self.enter_cell_text(2, 1, '10')
        self.enter_cell_text(2, 2, '={1 -> B1}[1]')
        self.wait_for_cell_value(2, 2, '10')

        # and this
        self.enter_cell_text(3, 1, '10')
        self.enter_cell_text(3, 2, '=(lambda x -> C1 * x)(2)')
        self.wait_for_cell_value(3, 2, '20')

