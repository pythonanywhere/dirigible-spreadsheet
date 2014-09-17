# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest, Url


class Test_2602_SheetPageShouldDisplayBeforeFirstRecalcComplete(FunctionalTest):

    def test_sheet_page_displays_fast(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()
        sheet_page = self.browser.current_url

        # * He sets it up so that it takes 30 seconds to recalc.
        self.enter_cell_text(1, 2, '=123')
        self.enter_usercode(dedent("""
            import time
            time.sleep(30.0)
            load_constants(worksheet)
            evaluate_formulae(worksheet)
            worksheet[2,2].value = 'usercode completed'
        """))
        self.wait_for_cell_value(2, 2, 'usercode completed', timeout_seconds=35)
        self.wait_for_cell_value(1, 2, '123')

        # * He navigates to a different page.
        self.go_to_url(Url.ROOT)

        # * He goes back to the sheet page.
        self.go_to_url(sheet_page)

        # * He notes that the grid takes less than 10 seconds to appear.
        self.wait_for_grid_to_appear(timeout_seconds=10)

        # * Once the grid is loaded, but before the recalc has completed, it
        #   displays the results of his formulae and usercode-only values
        #   even before the recalc is complete
        self.wait_for_cell_value(1, 2, '123', timeout_seconds=35)
        self.wait_for_cell_value(2, 2, 'usercode completed')
