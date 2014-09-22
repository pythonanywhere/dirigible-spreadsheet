# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import re
import time
from urlparse import urlparse
from textwrap import dedent

from browser_settings import SERVER_IP

from functionaltest import FunctionalTest, snapshot_on_error


class Test_2532_LambdasInCells(FunctionalTest):

    @snapshot_on_error
    def test_lambda_in_cell(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters "=lambda x -> x + 1" in A1.
        self.enter_cell_text(1, 1, '=lambda x -> x + 1')

        # * He enters =A1(5) into B1
        self.enter_cell_text(2, 1, '=A1(5)')

        # * and notes that the value in B1 is 6
        self.wait_for_cell_value(2, 1, '6')

