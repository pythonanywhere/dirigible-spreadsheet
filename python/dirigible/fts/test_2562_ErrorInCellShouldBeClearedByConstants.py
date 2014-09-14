# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class test_2562_ErrorInCellShouldBeClearedByConstants(FunctionalTest):

    def test_ConstantsClearCellErrors(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters and error in A1.
        self.enter_cell_text(1, 1, '=1/0')
        self.assert_cell_has_error(1, 1, "ZeroDivisionError: float division")

        # * when he overwrites the cell content with a constant
        #   the error disappears
        self.enter_cell_text(1, 1, '123')
        self.assert_cell_has_no_error(1, 1)

        # hooray!

