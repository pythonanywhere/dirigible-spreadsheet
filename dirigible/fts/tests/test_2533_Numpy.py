# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest, snapshot_on_error


class Test_2533_Numpy(FunctionalTest):

    @snapshot_on_error
    def test_numpy_tutorial_create_arrays(self):
        # * Harold wants to do the tutorial at http://www.scipy.org/Tentative_NumPy_Tutorial
        #   in Dirigible
        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * At the start of the user code, he imports numpy
        self.prepend_usercode('import numpy')

        # * He creates a numoy array in cell A1
        self.enter_cell_text(1, 1, '=numpy.array([2, 3, 4])')

        # * He sees A1 contains the string array([2, 3, 4])
        self.wait_for_cell_value(1, 1, '[2 3 4]')

        # * He checks the type of the array in A2
        self.enter_cell_text(1, 2, '=type(A1)')
        self.wait_for_cell_value(1, 2, "<type 'numpy.ndarray'>")

        # * He creates a 2-dimensional array in B1
        self.enter_cell_text(2, 1, '=numpy.array([(1.5, 2, 3), (4, 5, 6)])')
        self.wait_for_cell_value(2, 1, "[[ 1.5 2. 3. ] [ 4. 5. 6. ]]")

        # * He has a look at some of the properties of the new array
        self.enter_cell_text(2, 2, '=B1.ndim')
        self.wait_for_cell_value(2, 2, "2")
        self.enter_cell_text(2, 3, '=B1.shape')
        self.wait_for_cell_value(2, 3, "(2, 3)")
        self.enter_cell_text(2, 4, '=B1.dtype')
        self.wait_for_cell_value(2, 4, "float64")
        self.enter_cell_text(2, 5, '=B1.itemsize')
        self.wait_for_cell_value(2, 5, "8")

        # * He creates an array of complex numbers
        self.enter_cell_text(3, 1, '=numpy.array([[1, 2], [3, 4]], dtype=numpy.complex)')
        self.wait_for_cell_value(3, 1, "[[ 1.+0.j 2.+0.j] [ 3.+0.j 4.+0.j]]")

        # * He creates arrays of zeros and ones
        self.enter_cell_text(4, 1, '=numpy.zeros((3, 4))')
        self.wait_for_cell_value(4, 1, "[[ 0. 0. 0. 0.] [ 0. 0. 0. 0.] [ 0. 0. 0. 0.]]")
        self.enter_cell_text(5, 1, '=numpy.ones((2, 3, 4), dtype=numpy.int16)')
        self.wait_for_cell_value(5, 1, "[[[1 1 1 1] [1 1 1 1] [1 1 1 1]] [[1 1 1 1] [1 1 1 1] [1 1 1 1]]]")

        # * He uses arange to create a list of numbers
        self.enter_cell_text(6, 1, '=numpy.arange(10, 30, 5)')
        self.wait_for_cell_value(6, 1, "[10 15 20 25]")

        # * He creates a sequence of floating point numbers
        self.enter_cell_text(7, 1, '=numpy.linspace(0, 2, 9)')
        self.wait_for_cell_value(7, 1, "[ 0. 0.25 0.5 0.75 1. 1.25 1.5 1.75 2. ]")

        # * He uses arange to create a very large array and notes that Dirigible displays it semi-intelligently
        self.enter_cell_text(8, 1, '=numpy.arange(10000)')
        self.wait_for_cell_value(8, 1, "[ 0 1 2 ..., 9997 9998 9999]")


    @snapshot_on_error
    def test_numpy_tutorial_basic_operations(self):
        # * Harold wants to do the tutorial at http://www.scipy.org/Tentative_NumPy_Tutorial
        #   in Dirigible
        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * At the start of the user code, he imports numpy
        self.prepend_usercode('import numpy')

        # * He deducts one range from another
        self.enter_cell_text(1, 1, '=numpy.array([20, 30, 40, 50])')
        self.enter_cell_text(2, 1, '=numpy.arange(4)')
        self.enter_cell_text(3, 1, '=a1 - B1')
        self.wait_for_cell_value(3, 1, "[20 29 38 47]")

        # * He squares a range
        self.enter_cell_text(3, 2, '=B1**2')
        self.wait_for_cell_value(3, 2, "[0 1 4 9]")

        # * He takes the sine of a range
        self.enter_cell_text(3, 3, '=10*numpy.sin(a1)')
        self.wait_for_cell_value(3, 3, "[ 9.12945251 -9.88031624 7.4511316 -2.62374854]")

        # * Having decided that Dirigible supports the basic operations to his satisfaction,
        #   he skips ahead to check that it works with complex numbers
        self.enter_cell_text(1, 1, '=numpy.ones(3, dtype=numpy.int32)')
        self.enter_cell_text(2, 1, '=numpy.linspace(0, numpy.pi, 3)')
        self.enter_cell_text(2, 2, '=b1.dtype.name')
        self.wait_for_cell_value(2, 2, "float64")
        self.enter_cell_text(3, 1, '=a1+b1')
        self.wait_for_cell_value(3, 1, "[ 1. 2.57079633 4.14159265]")
        self.enter_cell_text(3, 2, '=c1.dtype.name')
        self.wait_for_cell_value(3, 2, "float64")
        self.enter_cell_text(4, 1, '=numpy.exp(c1 * 1j)')
        self.wait_for_cell_value(4, 1, "[ 0.54030231+0.84147098j -0.84147098+0.54030231j -0.54030231-0.84147098j]")
        self.enter_cell_text(4, 2, '=d1.dtype.name')
        self.wait_for_cell_value(4, 2, "complex128")
