# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest


class Test_2691_AllowSettingValuesFromUsercodeBeforeLoadConstants(FunctionalTest):

    def test_load_constants_doesnt_trash_cells(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He adds stuff to the start of the usercode to set a value on a cell, before load_constants
        #   (which previously erroneously cleared cells with no set formula)
        self.prepend_usercode(dedent("""
            worksheet[1, 1].value = 'wibble'
        """))

        # * When the recalc is completed, the cell shows the value
        self.wait_for_cell_value(1, 1, 'wibble')