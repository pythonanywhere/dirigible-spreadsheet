# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2601_UndefinedShouldBeAvailableToUsercode(FunctionalTest):

    def test_use_undefined(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He uses undefined in A1.
        self.enter_cell_text(1, 1, '=A2==undefined')
        self.wait_for_cell_value(1, 1, 'True')
        self.assert_cell_has_no_error(1, 1)

        # * he uses undefined in usercode
        self.append_usercode('worksheet[1,3].value = worksheet[1,4].value==undefined')
        self.wait_for_cell_value(1, 3, 'True')
        self.assertTrue(self.get_console_content().startswith('Took'))

        # hooray!

