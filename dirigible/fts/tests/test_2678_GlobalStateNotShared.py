# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, snapshot_on_error, Url

from textwrap import dedent

class Test_2678_GlobalStateNotShared(FunctionalTest):

    @snapshot_on_error
    def test_global_state_not_shared(self):
        # * Harold logs in to Dirigible
        self.login()

        # * Switching with inhuman speed between several browser windows,
        #   in each he creates a new sheet with a unique identifier and
        #   user code that adds the identifier to sys.path
        try:
            number_of_windows = 5

            window_ids = []
            for sheet_number in range(number_of_windows):
                window_id = "sheet_window_%s" % (sheet_number,)
                self.selenium.open_window(Url.NEW_SHEET, window_id)
                self.selenium.wait_for_pop_up(window_id, timeout=20000)
                self.selenium.select_window(window_id)
                self.wait_for_grid_to_appear()
                self.append_usercode(dedent('''
                    import sys
                    sys.path.append(%r)
                    worksheet[2, 1].value = %r
                    worksheet[1, 1].value = sys.path''' % (window_id, window_id)))
                window_ids.append(window_id)

            # He ensures that they all finish the recalc
            for window_id in window_ids:
                self.selenium.select_window(window_id)
                self.wait_for_cell_value(2, 1, window_id, timeout_seconds=30)
                self.wait_for_console_content('')
                sys_path_str = self.get_cell_text(1, 1)
                self.assertTrue(window_id in sys_path_str)
                for w_id in window_ids:
                    if w_id == window_id: continue
                    if w_id in sys_path_str:
                        self.fail('Window %r had the sys.path from window %r: %r' % (window_id, w_id, sys_path_str))
        finally:
            # Back to our main window
            #self.selenium.select_window(0)
            pass
