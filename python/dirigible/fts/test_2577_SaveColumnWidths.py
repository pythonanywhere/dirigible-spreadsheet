# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent
import time

from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT


DELTA = 30

class Test_2537_save_column_widths(FunctionalTest):


    def get_column_header_locator(self, column_name):
        return 'css=div[title=%s]' % (column_name,)


    def get_column_resize_handle_locator(self, column_name):
        return "%s div.slick-resizable-handle" % (self.get_column_header_locator(column_name),)


    def get_column_width(self, column_name):
        return self.selenium.get_element_width(self.get_column_header_locator(column_name))


    def wait_for_column_width(self, column_name, width):
        self.wait_for(
            lambda: self.get_column_width(column_name) == width,
            lambda: 'column %s width to become %s (was %s)' % (column_name, width, self.get_column_width(column_name))
        )


    def resize_column(self, column_name, width_delta):
        orig_column_width = self.get_column_width(column_name)

        self.selenium.drag_and_drop(
            self.get_column_resize_handle_locator(column_name),
            '%d,+0' % (width_delta,)
        )

        self.wait_for_column_width(column_name, orig_column_width + width_delta)



    def test_save_em(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # He resizes a column
        self.resize_column('B', 30)

        new_size = self.get_column_width('B')

        # * He refreshes the page
        self.refresh_sheet_page()

        # * the resized column is still enbiggenened
        self.wait_for_grid_to_appear()
        self.wait_for_column_width('B', new_size)



    def test_changing_column_widths_does_not_interrupt_recalc_but_does_save_widths(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He sets up a long recalc
        self.enter_cell_text(1, 1, '1')
        self.append_usercode(dedent('''
        worksheet[1, 1].value += 1
        import time
        time.sleep(30)
        '''))

        # * After it's been running for a while, but before it is finished,
        #   he plays with the column widths.  (Waiting for this makes sure that
        #   we can distinguish between the completion of the first recalc (which
        #   should happen within the time the usercode takes to execute plus or
        #   minus a bit) and the completion of a second recalc that was somehow
        #   triggered by broken column-resize code; resizing columns should
        #   *not* trigger a recalc.)
        time.sleep(20)
        self.resize_column('B', 30)
        col_b_width = self.get_column_width('B')
        self.resize_column('C', -10)
        col_c_width = self.get_column_width('C')

        # * and notes that the recalc completes normally -- ie.
        #   that when it completed it did not see the updated
        #   column widths and think that the sheet had changed
        #   underneath it, and thus abort and send back an error
        #   -- and also that it completes within <usercode-time>
        #   from the initial setting of the usercode, not within
        #   a larger amount of time (which would imply that setting
        #   column widths triggered a recalc.
        self.wait_for_cell_value(1, 1, '2', timeout_seconds=15)

        # * He then refreshes the page to make sure that the recalc
        #   that just finished copied the new column widths to the DB.
        self.refresh_sheet_page()
        self.wait_for_grid_to_appear()
        self.wait_for_column_width('B', col_b_width)
        self.wait_for_column_width('C', col_c_width)
