# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import re
from textwrap import dedent

from functionaltest import FunctionalTest


class Test_2704_OldStyleClassesInTheGrid(FunctionalTest):

    def test_put_old_style_classes_in_grid(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He defines an old-style class in the usercode
        self.enter_usercode(dedent('''
            class Basilisk():
                pass
            load_constants(worksheet)
            evaluate_formulae(worksheet)
        '''))

        # * He puts an instance of it in the grid
        self.enter_cell_text(1, 1, "=Basilisk()")

        # * The formatted value is something sane.
        self.wait_for_cell_value(1, 1, re.compile(r'<__builtin__.Basilisk instance at 0x.*>'))

        # * He references the class itself from another cell, just for kicks.
        self.enter_cell_text(1, 2, "=Basilisk")

        # * The formatted value is equally sane.
        self.wait_for_cell_value(1, 2, '__builtin__.Basilisk')

        # * He refreshes the page.
        self.selenium.refresh()
        self.wait_for_grid_to_appear()

        # * Everything still looks OK.
        self.wait_for_cell_value(1, 1, re.compile(r'<__builtin__.Basilisk instance at 0x.*>'))
        self.wait_for_cell_value(1, 2, '__builtin__.Basilisk')

        # * Disappointed at not being about to break Dirigible, he goes out to take
        #   potshots at the Goodyear blimp with a shotgun.
