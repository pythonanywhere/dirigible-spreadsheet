# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest


class Test_2781_FormulaAndFormattedValueMustBeStrings(FunctionalTest):

    def test_str_formula_and_formatted_value(self):
        # * Harold wants to be perverse and do strange and unnatural things
        #   to cells.
        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He sets the formula to an object that he made
        self.enter_usercode(dedent('''
            class HaroldsObject(object):
                pass

            worksheet.A1.formula = HaroldsObject()
        '''))

        # * Dirigible complains.
        self.wait_for_console_content(
            'TypeError: cell formula must be str or unicode\n    User code line 5'
        )

        # * He tries to molest the formatted_value instead
        self.enter_usercode(dedent('''
            class HaroldsObject(object):
                pass

            worksheet.A1.formatted_value = HaroldsObject()
        '''))

        self.wait_for_console_content(
            'TypeError: cell formatted_value must be str or unicode\n    User code line 5'
        )
