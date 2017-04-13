Dirigible, the web-based Pythonic Spreadsheet
=============================================

This is the source code from the end-of-lifed https://www.projectdirigible.com project, preserved for posterity and the curious


Installation instructions
-------------------------

    cd dirigible
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser  # make yourself a user account.
    python manage.py runserver

And visit http://localhost:8000

Security
--------

This version of Dirigible has absolutely no security, so bewarned, before you put this on a public server -- anyone that logs in has the full access permissions of whichever user is running django, and you can use Python to do pretty much whatever you want!

Check out the chroot_recalculation branch for a slightly more secure approach


Some minimal context
--------------------

(Probably best to play around with the spreadsheet a bit before reading this guide, to get an idea of what is possible.  Try creating a couple of formulae with calculations, and maybe using a user-defined function from the usercode panel)

* A Dirigible spreadsheet is "just" a python program, which is visible in the usercode panel on the right.  

* Recalculating the spreadsheet means executing that code, including two very important built-in functions:  `load_constants` and `evaluate_formulae`.  

In between those two functions, the user can add their own arbitrary code. 

One global object is accessible, the `worksheet` ([source](https://github.com/pythonanywhere/dirigible-spreadsheet/blob/master/dirigible/sheet/worksheet.py))

A worksheet is compose of cells (it is in fact a dictionary, whose keys are the location, expressed as a tuple of column,row, and whose values are cell objects)

A cell ([source](https://github.com/pythonanywhere/dirigible-spreadsheet/blob/master/dirigible/sheet/cell.py)) has two key attributes:

- its `formula`, which may just be a constant like "hello" or "12,3", or a formula, like =A1+B1
- its `value`, which is the result of evaluating the formula.  

If the formula is a constant, its value is that constant.

If it's a real formula, then it will be evaluated as part of `evaluate_formulae()`.  This involves:

1. Parsing the formula ([source](https://github.com/pythonanywhere/dirigible-spreadsheet/blob/master/dirigible/sheet/formula_interpreter.py))
    - cell formulae can include any valid python, as well as
    - special spreadsheet syntax, including cell references like A1 or B2, and special spreadsheet formulae like the SUM function
    - any special spreadsheet syntax is parsed and converted to Python
    - and finding out the `dependencies`.  If the formula for cell A1 includes a reference to B1, then B1 is a dependency of A1

2. Placing it into the whole spreadsheet's dependency graph ([source](https://github.com/pythonanywhere/dirigible-spreadsheet/blob/master/dirigible/sheet/dependency_graph.py))

3. Evaluating all the branches of that graph, starting from its leaves, by evaluating the cell's formula to get its value.  That can then be fed into cells that depend on it, and so on.  (See [calculate.py](https://github.com/pythonanywhere/dirigible-spreadsheet/blob/master/dirigible/sheet/calculate.py))

Cell formulae can also use any user-defined functions from the usercode.


Everything else is fairly peripheral.  There is some monkeying around with json, some stuff with threads that's a throwback to some parallelisation features that I haven't finished removing.

Questions and requests for clarification are solicited, as are any pull requests for documentation, bugfixes, fixes to unit tests (of which all but three were passing in this modified version of our codebase, at the time of writing), or FTs (half-ported from old selenium)

