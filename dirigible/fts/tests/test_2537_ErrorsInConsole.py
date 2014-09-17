# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#
from functionaltest import FunctionalTest

from textwrap import dedent

class Test_2537_ErrorsInConsole(FunctionalTest):

    def test_console(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He notes that there is a console on the page
        self.is_element_present('id=id_console')

        original_usercode = self.get_usercode()

        # * He makes an error in usercode
        self.prepend_usercode(dedent('''
        def fn():
            x = new_value
        '''))
        self.append_usercode(dedent('''
        fn()'''))
        fn_call_line = len(self.get_usercode().split('\n'))

        expected_traceback = '''NameError: global name 'new_value' is not defined
    User code line %d
    User code line 2, in fn''' % (fn_call_line,)

        # * ... and notes that a useful traceback appears in the console
        self.wait_for_console_content(expected_traceback)

        # * He removes his error, saves his usercode and notes that the error is no longer shown
        self.enter_usercode(original_usercode)
        self.wait_for_console_content("")


    def test_formula_error_in_console(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some formulae that contain errors
        self.enter_cell_text(1, 1, '=1/0')
        self.enter_cell_text(3, 2, '=newvalue')
        self.enter_cell_text(2, 4, '={"a": 2}')
        self.assert_cell_has_error(1, 1, 'ZeroDivisionError: float division')

        # * He notes that the errors are reported in the console
        expected_tracebacks = ('''NameError: name 'newvalue' is not defined
    Formula '=newvalue' in C2''',
        '''ZeroDivisionError: float division
    Formula '=1/0' in A1''',
        '''FormulaError: Error in formula at position 6: unexpected ': '
    Formula '={"a": 2}' in B4''')
        for expected_traceback in expected_tracebacks:
            self.wait_for_console_content(expected_traceback)

        # * He removes the errors and notes that the traceback is cleared
        self.enter_cell_text(1, 1, '=1')
        self.enter_cell_text(3, 2, '')
        self.enter_cell_text(2, 4, '={"a"-> 2}')
        self.wait_for_cell_value(1, 1, '1')
        self.wait_for_console_content("")


    def test_formula_errors_precede_usercode_errors_in_console(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters a formula with an error
        self.enter_cell_text(1, 1, '=1/0')

        # * and breaks the usercode after the formulae are run
        self.append_usercode('x = y')
        error_line = len(self.get_usercode().split('\n'))

        # * and notes that the errors are reported in the expected order
        expected_traceback = '''ZeroDivisionError: float division
    Formula '=1/0' in A1
NameError: name 'y' is not defined
    User code line %d''' % (error_line,)
        self.wait_for_console_content(expected_traceback)

