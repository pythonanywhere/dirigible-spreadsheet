# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2554_SlicingInFormulae(FunctionalTest):

    def test_formulas_work_properly(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # Harold REALLY likes slicing things. We should ensure that
        # he can indulge his axe-murderer side
        self.enter_cell_text(1, 1, '=[0, 10, 20, 30, 40]')
        self.enter_cell_text(1, 2, '=A1[1->3]')
        self.wait_for_cell_value(1, 2, '[10, 20]')

        self.enter_cell_text(2, 1, 'a string that really needs to be sliced')
        self.enter_cell_text(2, 2, '=B1[->10]')
        self.wait_for_cell_value(2, 2, 'a string t')

        self.enter_cell_text(3, 2, '=B1[9->]')
        self.wait_for_cell_value(3, 2, 'that really needs to be sliced')

        self.enter_cell_text(4, 2, '=B1[-8->]')
        self.wait_for_cell_value(4, 2, 'e sliced')

        self.enter_cell_text(5, 2, '=B1[4->->3]')
        self.wait_for_cell_value(5, 2, 'rgh ayesoele')
