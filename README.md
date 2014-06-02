Dirigible, the web-based Pythonic Spreadsheet
=============================================

This is the source code from the end-of-lifed https://www.projectdirigible.com project, preserved for posterity and the curious


Installation instructions
-------------------------

We never designed it for portability I'm afraid, so this is a little yucky, but:

- Copy the source into a folder at `/home/dirigible`  (this path is hard-coded)
- `sudo pip install -r /home/dirigible/python/dirigible/requirements.txt` (the python dependencies must be installed system-wide)
- `sudo python /home/dirigible/python/dirigible/manage.py runserver`

And visit http://localhost:8000


