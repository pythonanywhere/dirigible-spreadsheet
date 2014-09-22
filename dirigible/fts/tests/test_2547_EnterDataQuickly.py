# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import time

from functionaltest import FunctionalTest, snapshot_on_error


class Test_2547_EnterDataQuickly(FunctionalTest):

    @snapshot_on_error
    def test_enter_data_quickly(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters 20 numbers quickly
        for row in range(1, 21):
            self.enter_cell_text_unhumanized(1, row, "%s" % (row,))

        # * He checks that they are all there.
        for row in range(1, 21):
            self.wait_for_cell_value(1, row, "%s" % (row,))


    @snapshot_on_error
    def test_enter_data_quickly_in_batches(self):
        # Running the above test made it clear that it was significantly more
        # likely to drop the last number than any others, so we added the below
        # to increase the likelihood of that particular failure mode.

        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters 20 numbers quickly, taking a brief rest every five numbers
        for row in range(1, 21):
            self.enter_cell_text_unhumanized(1, row, "%s" % (row,))
            if row % 5 == 0:
                time.sleep(2)

        # * He checks that they are all there.
        for row in range(1, 21):
            self.wait_for_cell_value(1, row, "%s" % (row,))

