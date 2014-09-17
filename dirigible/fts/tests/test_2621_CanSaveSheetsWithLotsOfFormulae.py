# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest, snapshot_on_error


class Test_2621_CanSaveSheetsWithLotsOfFormulae(FunctionalTest):

    @snapshot_on_error
    def test_can_save_lots_of_formulae(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()
        sheet_page = self.browser.current_url

        # * Typing tirelessly, he enters moderately-sized formulae in
        #   23 columns across 400 rows
        cell_value = "a" * 5
        self.enter_usercode(dedent("""
            for col in range(1, 45):
                for row in range(1, 401):
                    worksheet[col, row].formula = %r
        """ % cell_value))
        self.wait_for_cell_shown_formula(1, 1, cell_value, timeout_seconds=30)
        self.enter_usercode(dedent("""
            load_constants(worksheet)
            evaluate_formulae(worksheet)
        """))

        # * He looks at the grid and sees that the data appear to be
        #   there
        self.wait_for_cell_value(1, 1, cell_value, timeout_seconds=30)
        self.wait_for_cell_value(1, 10, cell_value)
        self.wait_for_cell_value(10, 1, cell_value)
        self.wait_for_cell_value(10, 10, cell_value)
        self.wait_for_cell_value(5, 5, cell_value)

        # * He goes back to his dashboard.
        self.go_to_url(sheet_page)

        # * He returns to the grid, and is pleased to see that the data
        #   are still there.
        self.wait_for_cell_value(1, 1, cell_value, timeout_seconds=30)
        self.wait_for_cell_value(1, 10, cell_value)
        self.wait_for_cell_value(10, 1, cell_value)
        self.wait_for_cell_value(10, 10, cell_value)
        self.wait_for_cell_value(5, 5, cell_value)
