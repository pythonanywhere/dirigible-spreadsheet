# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest


class Test_2582_ReferencingEmptyCell(FunctionalTest):

    def test_referencing_empty_cell(self):
        # Harold logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # He enters "=A1" into B1
        self.enter_cell_text(2, 1, '=A1')

        # He sees that B1 is in its "I have no value but my formula is '=A1'" state.
        self.wait_for_cell_shown_formula(2, 1, '=A1')

        # Cell A1 is blank.
        self.wait_for_cell_value(1, 1, '')
        self.wait_for_spinner_to_stop()

        # There is nothing in the error console.
        self.assertTrue(
            self.get_console_content().startswith('Took'),
            "Unexpected error console content:\n%r" % (self.get_console_content(),)
        )

        # He adds code to set the value of C1 to the end of the user code.
        self.append_usercode("worksheet[3, 1].value = 23")

        # He notes that it is being executed.
        self.wait_for_cell_value(3, 1, '23')
