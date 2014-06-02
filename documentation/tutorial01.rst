Tutorial part 1: First steps, adding Python to a spreadsheet
============================================================

This tutorial aims to get you started with Dirigible as quickly as possible.

It is made up of a number of examples of increasing complexity, each of which
shows one or more useful Dirigible features -- this page contains the first.


Writing your first Dirigible spreadsheet
----------------------------------------

The first spreadsheet we'll build using Dirigible is a very simple price list,
with a few useful functions.  Our aim is just to give you a taste of how
Dirigible differs from traditional spreadsheet programming.  We'll move on to
more interesting examples in a later tutorial.

We'll also assume that you have at least a basic knowledge of programming; if
you can code Python, C#, Java, Perl, C, C++, or something similar reasonably
well, you should be fine.

We strongly recommend that you create your own sheet by working through this
tutorial.


Creating the sheet
^^^^^^^^^^^^^^^^^^

The first page that you see when you log in to Dirigible is your *dashboard*, a
page that summarises all of the details of your Dirigible account.  It will
look something like this:

.. image:: tutorial-01-dashboard.png

Here you can see a list of all of your spreadsheets; if you've only just signed
up, the list will be pretty short!  You can always access your dashboard from
anywhere within Dirigible by using the "My account" link at the top right of
the page.

To get started with this tutorial, click the "Create new sheet" link at the top
right of the list of spreadsheets.  You'll be taken to a new page, showing an
empty spreadsheet:

.. image:: tutorial-01-sheet-page.png

We'll call this the *sheet page*.  Its layout should be pretty
self-explanatory; there's some navigational stuff at the top, the name of the
sheet (which will initially be something like "Sheet 111") , and then a
spreadsheet grid on the left-hand side and a code editor on the right.  The
spreadsheet grid is where you enter data and formulae, just as you would in any
spreadsheet.  The code editor is where you enter your own Python code to
augment and control the recalculation of the spreadsheet; we call this
*usercode*, and you'll find out more about it later.  Underneath the usercode
editor is the output window; more about that later too.


Some basic setup
^^^^^^^^^^^^^^^^

Before we enter any data into the sheet, let's customize it a little.  If you
move the mouse over the sheet name then you'll see its background go grey.
Click it, and you will be able to edit it.  Type ``Price list`` and hit return
to change it.

Next, let's edit the usercode a little.  Initially, this has calls to two
functions, :func:`load_constants` and :func:`evaluate_formulae`.
There'll be more about these later, but for now, all you need to know is that
they are important, and you shouldn't delete them!

There are also some comments -- lines starting with ``#``.  For now, we'll just
add a new comment to the top.  Click just before the call to
:func:`load_constants`, add a few blank lines, and then enter the following:

::

    # Tutorial, example 1
    # Price list
    # Written by YOUR NAME on DATE.

Now, click back in the spreadsheet grid.  Because the only change you've made
is adding a few comments, nothing else should have changed.

.. image:: tutorial-01-after-basic-setup.png

Let's add some data to the table.

Entering data
^^^^^^^^^^^^^

Click on cell A1 in the grid, and type ``Product``.  Hit the tab key to move on
to cell B1, and type ``Net price`` -- note that while you type, the text
appears both in the cell and in the formula bar above the grid, just like in
any other spreadsheet.  Tab again to C1, and enter ``Gross price``, then hit
return.  Use the cursor keys or the mouse to move to cell A2, and type the
following products for our price list (hitting enter after each):

* Paper
* Printer ink
* Printer cables
* AA batteries
* Pens
* Notepads

Once you've done this, adjust the widths of columns A and C so that everything
fits; if you move the mouse pointer over the header between columns A and B,
you should see it turn into a double-headed arrow; click and drag at that point
to adjust column A's width, and then do the same for column C so that all of
the text "Gross price" is visible.  Once that's done, you should have a
spreadsheet that looks something like this:

.. image:: tutorial-01-products.png

Finally, put some net prices (that is, the price of each product before sales
tax) into column B:

.. image:: tutorial-01-net-prices.png

Adding a formula
^^^^^^^^^^^^^^^^

Now that we've got some data in the grid, let's add a formula.  Click on cell
C2, and enter our first attempt at a calculation to add the tax to the gross
price.  We'll use a tax rate of 17.5%, so the formula needs to be ``=B2 *
1.175``; type that in, and hit return.

.. image:: tutorial-01-gross-price-1.png

Now, this worked, but it's started to make the spreadsheet a bit opaque.  What
would happen if the tax rate changed?  Finding which formulae across many cells
referenced the value 1.175 would be error-prone, especially if the spreadsheet
got bigger.  So let's change it and make sure we have a tax rate in just one
place.


Using usercode variables in formulae
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Edit the usercode, and just underneath where you put your comment earlier, add
this code:

::

    # Conversion factor for current tax rate
    tax_factor = 1.175

Now, double-click cell C2 and edit the formula so that it reads ``=B2 *
tax_factor``.  Hit return; the results should be unchanged, but now you can
change the tax by adjusting the user code.  Try changing ``tax_factor`` to,
say, 1.2 in the usercode, then save the change (by clicking on the grid or
pressing control-S) and you'll see the gross price in C2 change; change it back
to 1.175 and see the gross price change back.

But what if the tax situation were more complex?  UK sales tax, for example,
isn't charged on certain kinds of goods.  In situations like that, a simple
``tax_factor`` value isn't enough -- we need a function.

Using usercode functions in formulae
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Describing the details of any tax system in this tutorial would be boring and
unnecessary, so let's write a function to handle an imaginary country where
pens and paper are taxed at 5% and everything else is taxed at 15%.  Replace
the tax factor usercode with this function definition:

::

    stationery_tax_factor = 1.05
    other_tax_factor = 1.15
    def add_tax(product, price):
        if product.lower() in ("pens", "paper"):
            return price * stationery_tax_factor
        return price * other_tax_factor

As soon as you save the usercode, you'll see an error message appear in cell
C2.  If you move the mouse pointer over it, you should see a popup explaining
the problem:

.. image:: tutorial-01-error-in-grid.png

If you look down at the output console, in the bottom right, underneath the
usercode editor, you will see that the error is displayed there too:

.. image:: tutorial-01-error-in-output-console.png

All errors are shown in the output console, which can be very useful as your
spreadsheets get larger and cells containing errors are no longer necessarily
visible.

Anyway, the problem that is causing these errors is clear enough; our formula
still refers to the variable ``tax_factor``, which we have replaced with our
new function.  To fix the problem, double-click on C2 to edit its formula, and
change it to ``=add_tax(A2, B2)``.  The errors will disappear, and you'll see
the new value with the 5% stationery tax rate:

.. image:: tutorial-01-gross-price-2.png

Next, enter the equivalent formula into C3: ``=add_tax(A3, B3)``, and you'll
see that the printer ink gets the higher 15% tax:

.. image:: tutorial-01-gross-price-3.png

Now, we could enter similar formulae for every other cell in column C, but this
would be tedious.  We could copy the formula down, but then we'd be duplicating
code, so if we changed the formula later, we'd need to make the same change
multiple times.  As every programmer knows, when you do the same thing multiple
times, it's better to use a loop than to copy and paste things.

.. _generating-formulae:

Generating formulae from usercode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just underneath the usercode you've added but *before* the
``evaluate_formulae`` line, add the following:

::

    row = 2
    while (worksheet['A', row].formula and worksheet['B', row].formula):
        worksheet['C', row].formula = '=add_tax(A%d, B%d)' % (row, row)
        row += 1

This simple Python loop runs through the worksheet from row 2 downwards until
it encounters a blank row, and for each one it puts a formula like the one we
wrote earlier into column C.  Click back in the grid or hit control-S to save
the usercode change, and you'll see gross prices filled in for all of the
products.  Click on one of the cells in column C, and you'll see that the
formula there has the correct row numbers in it:

.. image:: tutorial-01-gross-price-4.png

Now, add a new row to the bottom of the list; put ``Staples`` into A8 and
``0.99`` into B8.  As soon as you hit return in cell B8, you'll see that the
gross price automatically gets its formula and the resulting value.

.. image:: tutorial-01-gross-price-5.png

And that's it for now!

In conclusion
^^^^^^^^^^^^^

In this part of the tutorial, we've shown how to use Dirigible like a normal
spreadsheet, and then extended that to show how you can interact with the
spreadsheet grid from usercode to make a more resilient, more extendable
calculation model.

In :doc:`the next part of the tutorial <tutorial02>`, we'll show how you can
perform much more advanced goal-seeking calculations by changing the simple
call to the :func:`evaluate_formulae` function that Dirigible gives you by
default.
