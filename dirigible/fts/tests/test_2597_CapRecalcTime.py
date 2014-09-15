# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest


class Test_2597_CapRecalcTime(FunctionalTest):

    def test_recalcs_get_stopped(self):
        # * Harold doesn't want to waste money on recalculations where he created an
        #   infinite loop. Dirigible helpfully kills any recalculations that are
        #   taking too long. The default (set in the database per sheet) is 60sec.

        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * and enters some ill-advised user-code
        self.append_usercode('while True: pass\n\n#some stuff')
        fn_call_line = self.get_usercode().split('\n').index('while True: pass')

        # * He notes that after a minute, there is a message in the console
        #   telling him that his recalculation timed out.
        self.wait_for_console_content(
            'TimeoutException: \n    User code line 10',
            timeout_seconds=59
        )

