# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest
from textwrap import dedent


class Test_2538_ShowStdoutInConsole(FunctionalTest):

    def test_stdout_displayed_in_console(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # He adds usercode to print a message
        self.prepend_usercode("print 'greetings'")
        self.append_usercode("print 'puny human'")
        self.wait_for_spinner_to_stop()

        expected = dedent('''
        greetings
        puny human''')[1:]
        self.wait_for_console_content(expected)


    def test_output_interleaved_with_formula_errors(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters usercode that executes evaluate_formulae and outputs a number of times
        self.enter_cell_text(1, 1, '=1/0')
        self.enter_usercode(dedent('''
            for x in range(2):
                print 'at %d' % (x,)
                evaluate_formulae(worksheet)
        '''))
        self.wait_for_spinner_to_stop()

        # * He notes that formula errors and output are correctly interleaved
        self.wait_for_console_content(dedent('''
        at 0
        ZeroDivisionError: float division
            Formula '=1/0' in A1
        at 1
        ZeroDivisionError: float division
            Formula '=1/0' in A1''')[1:])

        #   and that they are correctly coloured
        self.assertEquals(
            self.sanitise_console_content(self.selenium.get_eval("window.$('.console_output_text').text()")),
            dedent('''
                at 0
                at 1
            ''')[1:]
            )

        self.assertEquals(
            self.sanitise_console_content(self.selenium.get_eval("window.$('.console_error_text').text()")),
            dedent('''
                ZeroDivisionError: float division
                    Formula '=1/0' in A1
                ZeroDivisionError: float division
                    Formula '=1/0' in A1
            ''')[1:]
        )

