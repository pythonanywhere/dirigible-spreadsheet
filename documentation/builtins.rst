Built-in Dirigible classes and functions
========================================

The usercode you enter on the right-hand side of your Dirigible spreadsheet is there to *recalculate* the spreadsheet -- in other words, it takes a grid of *constants* like ``"23"`` and *formulae* like ``"=A1+A2"``, and turns it into a grid of *values* by evaluating the formulae in the context of the constants.

The default usercode does just enough of this to make Dirigible act like a traditional spreadsheet, but you can make it do much more by writing your own usercode.  This page describes the tools that Dirigible provides to do that; you can also use :doc:`other Python modules <python-modules>`.

The worksheet object
--------------------

.. data:: worksheet

    A variable bound to a :class:`Worksheet` object, populated with the data that you have set by editing the spreadsheet grid.  At the start of the usercode, ``worksheet`` will hold what you have entered; the formulae and constants.  It is the responsibility of the usercode to "recalculate" the spreadsheet to work out the resulting values.


.. class:: Worksheet

    An object that represents the contents of the spreadsheet grid.  One is created for you by the Dirigible runtime -- you can access it using the :const:`worksheet` variable -- but you can create your own too.  :class:`Worksheet` objects are also returned by the function :func:`run_worksheet`.

    The most useful thing you can do with a :class:`Worksheet` is access its cells, using any of the following forms::

        worksheet[2, 3]
        worksheet['B', 3]
        worksheet['B3']
        worksheet.B3


    All of the above give you a :class:`Cell` object representing the data that has been put into the spreadsheet grid at location B3.

    You can also ask the :class:`Worksheet` for a :class:`CellRange`:

    .. method:: Worksheet.cell_range(self, start_or_string_cellrange, end=None)

        If only ``start_or_string_cellrange`` is specified, treats it as the kind of cell range reference you might make in a formula (eg. ``F2:M13``) and returns the appropriate :class:`CellRange` object.  If two parameters are given, they are treated as two corners of the cell range, and can be either string cell references (eg. ``"B3"``) or "column, row" numerical tuples (eg. ``(2, 3)``).  Thus,
        the following are equivalent::

            my_range = worksheet.cell_range('B3:C10')
            my_range = worksheet.cell_range('B3', 'C10')
            my_range = worksheet.cell_range('B3', (3, 10))
            my_range = worksheet.cell_range((2, 3), 'C10')
            my_range = worksheet.cell_range((2, 3), (3, 10))


    .. attribute:: Worksheet.bounds

        Returns the outside coordinates for the used area of the worksheet, ie the leftmost-column, the highest-row, the rightmost-column and the lowest-row.  This is returned as a special ``tuple`` (left, top, right, bottom) of :class:`Bounds`, which has properties ``.left``, ``.top``, ``.right`` and ``.bottom``.  Thus, ``worksheet.bounds.top`` works.


Other available classes
-----------------------

.. class:: Cell

    An object that represents the contents of one cell in the spreadsheet grid.  It has a number of useful attributes:

    .. attribute:: Cell.formula

        The text that you can see and change when you edit the cell in the spreadsheet grid.  You can also set it from anywhere in your own usercode.  It is evaluated by calls to :func:`load_constants` or by :func:`evaluate_formulae`, depending on whether it starts with ``=``.

    .. attribute:: Cell.value

        The Python object that is the result of executing the cell's :attr:`formula`, used when evaluating other cells that depend on this cell.  If the :attr:`formula` does not start with ``=``, then this attribute will be set by :func:`load_constants`; if it *does* start with ``=``, then it will be set by :func:`evaluate_formulae`.  You can also set it yourself from your own code.  Setting a cell's :attr:`value` sets its :attr:`formatted_value` to a string representation of the new value.

    .. attribute:: Cell.formatted_value

        The text that you see for the cell in the grid when you are *not* editing it, so long as the cell has no :attr:`error`.  Normally this is a string representation of the :attr:`value`, but if you want to override the formatting then you can set it yourself from your own usercode.

    .. attribute:: Cell.error

        If this is set, the cell shows an error icon in the grid, like this:

        .. raw:: html

            <img src="/static/dirigible/images/error.gif" alt="A Dirigible error" /><br/><br/>


        The contents of this field appear in a help bubble when the mouse "hovers" over the cell.


    .. method:: Cell.clear

        Sets the :attr:`Cell.formula` and :attr:`Cell.error` to ``None``, the :attr:`Cell.value` to an instance of :class:`Undefined`, and the :attr:`Cell.formatted_value` to an empty string.


.. class:: CellRange

    An object that represents a rectangular block of cells within a worksheet.  Created using the :meth:`Worksheet.cell_range` convenience function.

    .. attribute:: CellRange.top

        The top of the :class:`CellRange` -- that is, its lowest row number.

    .. attribute:: CellRange.left

        The left of the :class:`CellRange` -- that is, its lowest column number.

    .. attribute:: CellRange.bottom

        The bottom of the :class:`CellRange` -- that is, its highest row number.

    .. attribute:: CellRange.right

        The right of the :class:`CellRange` -- that is, its highest column number.

    .. method:: CellRange.__len__(self, other)

        Normally accessed by calling ``len(cell_range)``.  Returns the total number of cells in the range, including empty ones.

    .. attribute:: CellRange.locations

        Returns an interator over each cell location in the :class:`CellRange`, running left-to-right, top-to-bottom.  For example, for the range ``B3:D4``, this would return the sequence (2, 3), (2, 3), (4, 3), (2, 4), (3, 4), (4, 4).

    .. method:: CellRange.__iter__

        Returns each value in the cells within the :class:`CellRange`, in the same order as :meth:`CellRange.locations`.  If a cell is empty, returns an :class:`Undefined` object.  Normally used with code such as the following::

            result = 5
            for value in worksheet.cell_range("B3:D4"):
                result = result * value + 2

    .. attribute:: CellRange.cells

        Returns the :class:`Cell` objects within the :class:`CellRange`, in the same order as :meth:`CellRange.locations`.

    .. attribute:: CellRange.locations_and_cells

        Returns a sequence of tuples comprising locations in the :class:`CellRange`, and the :class:`Cell` objects at those locations, in the same order as :meth:`CellRange.locations`.

    .. method:: __getitem__(self, location)
    .. method:: __setitem__(self, location, value)

        Get and set the :class:`Cell` objects at particular relative locations within the :class:`CellRange`.  The ``location`` must be a tuple of two numbers; (1, 1) is the top left of the cell range.

        For example, the following two lines would have the same effect::

            worksheet.D3.value = 23
            worksheet.cell_range("C2:D9")[2, 2].value = 23

    .. method:: clear(self)

        Clears the :class:`CellRange` by calling meth:`Cell.clear` on each of its cells.

    .. method:: CellRange.__eq__(self, other)

        Returns true iff ``other`` is a :class:`CellRange` with the same ``worksheet`` and top, left, bottom and right.

    .. method:: CellRange.__ne__(self, other)

        Identical to ``not`` :meth:`CellRange.__ne__`



.. class:: Undefined

    If the :attr:`Cell.value` of a :class:`Cell` has not been set yet, then it returns an instance of this class.



.. class:: Bounds

    Subclass of ``tuple`` representing the outside bounds of the used part of the worksheet.  Usually accessed via :attr:`Worksheet.bounds`. Contains 4 integers in the order ``(leftmost-column, topmost-row, rightmost-col, bottom-row))``.  These may also be accessed as ``.left``, ``.top``, ``.right``, ``.bottom``.


Special spreadsheet functions
-----------------------------

.. function:: load_constants(worksheet)

    Goes through all of the cells in the given ``worksheet``, looking at each one's :attr:`~.Cell.formula`.  If this *does not* start with ``=``, then this function works out what type it is -- number or string -- converts it to that type, and puts the result into the cell's :attr:`~.Cell.value` attribute.  For example, the formula ``"23"`` would be converted into the integer value ``23``, the formula ``"Hello, world"`` would just be copied directly over as a string, and the formula "=A1+A2" would be ignored by this function.

    Formulae that start with ``=`` are handled by :func:`evaluate_formulae`.


.. function:: evaluate_formulae(worksheet)

    Goes through all of the cells in the given ``worksheet``, looking at each one's :attr:`~.Cell.formula`.  If it *does* start with ``=``, then it is evaluated and the results are put into the the cell's :attr:`~.Cell.value` attribute.

    There are a number of interesting features of this function:

    * Dependency analysis.  The cells in the worksheet are evaluated in an order such that if cell *x* depends on cell *y*, then *y*'s formula is evaluated first.  For example, if A2 contains the formula ``=A1+2`` and A1 contains the formula ``=A3``, then A3 will be evaluated, then A1, then A2.
    * Cycle elimination.  If a "cycle" of mutually-dependent cells is found, they are not evaluated and the details of the cycle is put into each cell's :attr:`~.Cell.error`.  An example of a cycle: A1 has formula ``=A2`` and cell A2 has the formula ``=A1``.
    * Parallel recalculation.  If cells have no dependency, then they *may* be recalculated in parallel -- that is, at the same time.  This is useful when some cells take a long time to calculate -- for example, if they are calling :func:`run_worksheet` to execute calculations in another Dirigible spreadsheet -- because it allows your spreadsheet to get on with other calculations while awaiting a response.


.. function:: run_worksheet(worksheet_url, overrides=None)

    Accesses the target Dirigible worksheet at ``worksheet_url``, recalculates it, and returns the resulting :class:`Worksheet` object.  ``overrides`` is a dictionary containing formulae to put into the target worksheet before doing the recalculation; to override cell B3 with the value ``89`` you would use the dictionary ``{ (2, 3) : 89 }``

    This function helps you re-use your work.  For example, if you created a spreadsheet to calculate the value of a financial product, you might then use :func:`run_worksheet` in a different "portfolio" spreadsheet.  The portfolio would be a list of holdings of different products, and for each one if would use the original spreadsheet to work out the product's value.  The details of each product would be passed from spreadsheet to spreadsheet using the ``overrides`` dictionary.
