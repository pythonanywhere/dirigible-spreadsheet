# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2639_SciPy_and_MpMath(FunctionalTest):

    def test_can_use_scipy_norm(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # He imports scipy
        self.prepend_usercode("from scipy.stats import norm")

        # and accesses the cumulative normal distribution)
        # function from a number of cells, and gets the expected results
        self.enter_cell_text(1, 1, '=norm.cdf(-1000)')
        self.wait_for_cell_value(1, 1, '0.0')

        self.enter_cell_text(1, 2, '=norm.cdf(0)')
        self.wait_for_cell_value(1, 2, '0.5')

        self.enter_cell_text(1, 3, '=norm.cdf(1000)')
        self.wait_for_cell_value(1, 3, '1.0')


    def test_can_use_mpmath(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # He imports mpmath
        self.prepend_usercode("import mpmath")

        # and accesses the mpmath sin function
        self.enter_cell_text(2, 2, '=mpmath.libmp.BACKEND')
        self.enter_cell_text(1, 1, '=mpmath.sin(1)')
        self.wait_for_cell_value(1, 1, "0.841470984807897")
        self.wait_for_cell_value(2, 2, "gmpy")

