Differences Between Dirigible's Formula Language and Python
===========================================================

We call the syntax you use to enter formulae into the Dirigible spreadsheet grid the *formula language*.  It's almost exactly the same as Python expression syntax, but has some differences for compatibility with the formula syntax used in other spreadsheet applications.  (The Dirigible usercode, by contrast, is pure Python.)

This page highlights the differences between the formula language and normal Python.

"``:``" operator replaced by "``->``"
-------------------------------------

The colon ("``:``") is reserved for future use in cell ranges, e.g. ``C3:D8``.

All Python colons have been replaced by arrows ("``->``"). Lambdas, slices and dictionaries in the formula language are as follows:

    ::

        =lambda x -> x + 1
        =somelist[3->6]
        ={foo -> bar, baz -> qux}


List comprehensions: ``in`` clause trailing commas disallowed
-------------------------------------------------------------

Trailing commas for the Python list comprehension ``in`` clause are disallowed. For example, ``=[a for a in 1, 2,]`` is invalid because of the last comma.
