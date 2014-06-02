Technical overview
==================

This page explains the details of how your Dirigible models are recalculated.  It assumes you're familiar with the basics of what Dirigible is and does.  For a more gentle introduction, try the :doc:`tutorial01`.

When you editing a Dirigible model, you can put **formulae** and **constant values** into a spreadsheet grid, and you can edit Python **usercode** over on the right.  Every time you change something in the grid or modify the usercode, the model is recalculated and -- perhaps after a pause -- the updated values will appear.  This page explains exactly what goes on under the hood when that happens.

To recalculate the model, the server simply runs its usercode in a Python context containing a few "magic" functions and variables.  The data you've entered into the spreadsheet is not touched unless you have usercode that explicitly looks at it.  The default usercode is set up to manipulate the spreadsheet data so that it is processed like it would be in a traditional spreadsheet, but you could quite easily write usercode to process it in a completely different manner -- or to ignore it and simply use it as an input into your own code.

The three "magic" things that make the default behaviour possible are:

- The :const:`worksheet` object
- The :func:`load_constants` function
- The :func:`evaluate_formulae` function

They are described in detail on this page: :doc:`builtins`.
