# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest


class Test_2595_Throbber(FunctionalTest):

    def test_spinner_appears_during_recalcs(self):
        # * Harold likes to know when dirigible is working hard on his calculations

        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * When the grid has appeared, the spinner might be visible, but it disappears
        #   rapidly as the initial empty recalc completes.
        self.wait_for_spinner_to_stop()

        # * and enters some hard-working user-code
        self.append_usercode('import time\ntime.sleep(20)\nworksheet[1,1].value="ready"')

        # * He spots the spinner on the page
        self.wait_for(self.is_spinner_visible,
                      lambda : 'spinner not present',
                      timeout_seconds = 5)

        # * When the recalc is done, he sees the spinner go away
        self.wait_for_cell_value(1, 1, 'ready', timeout_seconds=25)

        self.assertTrue(self.is_element_present('css=#id_spinner_image.hidden'))
