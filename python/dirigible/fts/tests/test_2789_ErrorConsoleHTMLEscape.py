# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2789_ErrorConsoleHTMLEscape(FunctionalTest):

    def test_error_console_output_is_escaped(self):
        # Harold logs in to Dirigible and creates a new sheet and puts some super-sekrit data in it.
        self.login_and_create_new_sheet()

        # * He enters usercode that writes HTML to the error console
        self.append_usercode("print '<b>not bold</b>'")

        # * and notes that the result is correctly escaped
        self.wait_for_console_content("<b>not bold</b>")
