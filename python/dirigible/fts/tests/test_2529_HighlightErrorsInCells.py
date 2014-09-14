# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import re
import time
from urlparse import urlparse
from textwrap import dedent

from browser_settings import SERVER_IP

from functionaltest import FunctionalTest, snapshot_on_error


class Test_2529_HighlightErrorsInCells(FunctionalTest):
        
    def test_highlight_errors_in_cells(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters "=lambda x:x + 1" in A1.
        self.enter_cell_text(2, 3, '=lambda x:x + 1')

        # * and notes that there is an error marked for that cell
        self.assert_cell_has_error(2, 3,
            "FormulaError: Error in formula at position 10: unexpected ':'")

        # * He then enters '=my_value' in A2
        self.enter_cell_text(4, 5, '=my_value')

        # * and notes that A2 complains that my_value is not defined
        self.assert_cell_has_error(4, 5, "NameError: name 'my_value' is not defined")

        # * He fixes his errors and notes that the error markers go away
        self.enter_cell_text(2, 3, '=lambda x->x + 1')
        self.enter_cell_text(4, 5, '=10')
        self.wait_for_cell_value(4, 5, '10')

        self.assert_cell_has_no_error(2, 3)
        self.assert_cell_has_no_error(4, 5)


