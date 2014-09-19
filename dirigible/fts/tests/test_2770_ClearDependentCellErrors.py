# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2770_ClearDependentCellErrors(FunctionalTest):

    def test_dependent_cell_errors_are_cleared(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters "=1/0" into A1
        self.enter_cell_text(1, 1, '=1/0')
        self.wait_for_spinner_to_stop()
        # * He enters "=A1 + 1" into A2
        self.enter_cell_text(1, 2, '=A1 + 1')
        self.wait_for_spinner_to_stop()
        # * He enters "=A2 + 1" into A3
        self.enter_cell_text(1, 3, '=A2 + 1')
        self.wait_for_spinner_to_stop()

        # * He confirms that both A1 and A2 have errors
        self.assert_cell_has_error(1, 1, 'ZeroDivisionError: division by zero')
        self.assert_cell_has_error(
            1, 2,
            "TypeError: unsupported operand type(s) for +: 'Undefined' and 'int'"
        )
        self.assert_cell_has_error(
            1, 3,
            "TypeError: unsupported operand type(s) for +: 'Undefined' and 'int'"
        )

        # * He changes A1 to "=1"
        self.enter_cell_text(1, 1, '=1')

        # * A1's error will clear.
        self.wait_for_cell_value(1, 1, '1')
        # * A2's should too
        self.wait_for_cell_value(1, 2, '2')
        # * and A3's should too
        self.wait_for_cell_value(1, 3, '3')

