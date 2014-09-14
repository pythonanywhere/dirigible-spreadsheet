# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest, snapshot_on_error


class Test_2548_UserCode(FunctionalTest):

    @snapshot_on_error
    def test_editor_presence(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He notices that there is an Ace code editor on the page, which he
        #   has inexplicably not noticed before.
        self.assertTrue(
                self.selenium.is_element_present('css=#id_usercode.ace_editor')
        )

        # * In the editor, there is some interesting-looking code
        self.assertEquals(
            self.get_usercode(),
            dedent('''
                load_constants(worksheet)

                # Put code here if it needs to access constants in the spreadsheet
                # and to be accessed by the formulae.  Examples: imports,
                # user-defined functions and classes you want to use in cells.

                evaluate_formulae(worksheet)

                # Put code here if it needs to access the results of the formulae.
                ''').strip()
        )


    @snapshot_on_error
    def test_preformula_usercode(self):
        # * Harold wants to create a function to use in a cell's formula
        # * He logs in to Dirigible and creates a new sheet.
        self.login_and_create_new_sheet()

        # * He enters the following code into the usercode before the formula code:
        #{{{
        #def addA1(value):
        #    return value + worksheet.A1
        #}}}
        self.enter_usercode(dedent('''
            load_constants(worksheet)

            def addA1(value):
                return value + worksheet[1, 1].value

            evaluate_formulae(worksheet)
        '''))

        # * He enters '1' into A1
        self.enter_cell_text(1, 1, '1')

        # * In cell A4, he enters "=addA1(5)", and gets the result 6.
        self.enter_cell_text(1, 4, '=addA1(5)')
        self.wait_for_cell_value(1, 4, '6')


    @snapshot_on_error
    def test_postformula_usercode(self):
        # * Harold wants to specify code to run after his formulae have been calculated
        # * He logs in to Dirigible and creates a new sheet.
        self.login_and_create_new_sheet()

        # * He enters 2 into cell A3
        self.enter_cell_text(1, 3, '2')

        # * He adds an appropriate line to the end of the usercode, after the
        #   evaluate_formulae call, and applies the change:
        self.enter_usercode(dedent('''
            load_constants(worksheet)

            evaluate_formulae(worksheet)

            worksheet[1, 5].value = 10 + worksheet[1, 3].value
        '''))

        # * He notes that the value "13" appears in A5.
        self.wait_for_cell_value(1, 5, '12')
