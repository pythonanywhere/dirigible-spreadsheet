# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2848_WorksheetBounds(FunctionalTest):

    def test_access_worksheet_bounds(self):
        # * Harold logs in to Dirigible and creates a nice shiny new sheet
        self.login_and_create_new_sheet()

        # He enters some data
        self.enter_cell_text(4, 2, "Top right")
        self.enter_cell_text(2, 10, "Bottom left")

        # He writes some usercode to access the bounds of the worksheet
        self.append_usercode("worksheet[3, 5].value = worksheet.bounds")
        self.append_usercode("worksheet[3, 6].value = worksheet.bounds.bottom")

        # ...and is delighted to discover it works!
        self.wait_for_cell_value(3, 5, "(2, 2, 4, 10)")
        self.wait_for_cell_value(3, 6, "10")
