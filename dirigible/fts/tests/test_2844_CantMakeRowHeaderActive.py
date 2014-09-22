# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2844_CantMakeRowHeaderActive(FunctionalTest):

    def test_cant_make_row_header_active(self):
        ## Of course, this FT will have to go when we can select whole rows/cols.

        # * Harold logs in to Dirigible and creates a nice shiny new sheet
        self.login_and_create_new_sheet()

        # * He notes that A1 is the active cell
        self.wait_for_cell_to_become_active(1, 1)

        # * He clicks on the row header (column 0) for row 3.
        self.click_on_cell(0, 3)

        # * He notes that A1 is still the active cell
        self.wait_for_cell_to_become_active(1, 1)

        # * He does a small mouse drag within the header (column 0)
        self.mouse_drag((0, 3), (0, 4))

        # * He notes that A1 is still the active cell
        self.wait_for_cell_to_become_active(1, 1)

