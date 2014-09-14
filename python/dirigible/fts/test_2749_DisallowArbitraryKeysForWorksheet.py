# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2749_DisallowArbitraryKeysForWorksheet(FunctionalTest):

    def test_cant_use_silly_worksheet_keys(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He writes usercode to use a non-cell-reference key with the worksheet
        self.append_usercode("worksheet['fred'].value = 23")

        # * He gets an error
        self.wait_for_console_content("KeyError: 'fred' is not a valid cell location")
