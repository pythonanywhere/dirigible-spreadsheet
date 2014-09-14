# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest


class Test_2535_RunWorksheet(FunctionalTest):

    def test_run_worksheet_no_overrides(self):
        # * Harold logs in, creates a new sheet and notes its id
        self.login_and_create_new_sheet()
        target_sheet_url = self.selenium.get_location()

        # * and enters a few calculations and constants
        self.enter_cell_text(1, 1, '2')
        self.enter_cell_text(1, 2, '3')
        self.enter_cell_text(3, 3, '=A1 + A2')

        # * He creates another new sheet
        self.create_new_sheet()

        # * He enters =run_worksheet('http://...') into A1
        self.enter_cell_text(1, 1, '=run_worksheet("%s")' % (target_sheet_url,))

        # * He enters =A1[3, 3] into A2 and notes that
        self.enter_cell_text(1, 2, '=A1[3, 3].value')

        #   the value from C3 in the first sheet appears there
        self.wait_for_cell_value(1, 2, '5')


    def test_run_worksheet_with_overrides(self):
        # * Harold logs in, creates a new sheet and notes its id
        self.login_and_create_new_sheet()
        target_sheet_url = self.selenium.get_location()

        # * and enters a few calculations and constants
        self.enter_cell_text(1, 1, '2')
        self.enter_cell_text(1, 2, '3')
        self.enter_cell_text(3, 3, '=A1 + A2')

        # * He creates another new sheet
        self.create_new_sheet()

        # * He enters a run_worksheet with overrides into A1
        overrides = {
            (1, 1): 10,
            (1, 2): '43',
            (1, 3): '=str(A1)'
        }
        overrides_in_formula = repr(overrides).replace(':', '->')
        self.enter_cell_text(1, 1, '=run_worksheet("%s", %s)' % (target_sheet_url, overrides_in_formula))


        #   the value from C3 in the first sheet appears there
        # * He enters =A1[3, 3] into A2 and notes that
        self.enter_cell_text(1, 2, '=A1[3, 3].value')
        self.wait_for_cell_value(1, 2, '53')

        # * He also notes that A3 contains 10
        self.enter_cell_text(2, 2, '=A1[1, 3].value')
        self.wait_for_cell_value(2, 2, '10')


    def test_run_worksheet_with_error(self):
        # * Harold logs in, creates a new sheet and notes its id
        self.login_and_create_new_sheet()
        target_sheet_url = self.selenium.get_location()

        # * and enters an error
        self.prepend_usercode('import sys:')

        # * He creates another new sheet
        self.create_new_sheet()

        # * He enters a run_worksheet with overrides into A1
        overrides = {
            (1, 1): 10,
            (1, 2): '43',
            (1, 3): '=str(A1)'
        }
        overrides_in_formula = repr(overrides).replace(':', '->')
        self.enter_cell_text(1, 1, '=run_worksheet("%s", %s)' % (target_sheet_url, overrides_in_formula))

        # ... and notes the error shown in A1
        self.assert_cell_has_error(1, 1, 'Exception: run_worksheet: Syntax error at character 11')
