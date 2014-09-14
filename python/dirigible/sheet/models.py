# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from sheet.clipboard import Clipboard
from sheet.sheet import Sheet
from django.contrib.auth.models import User



def copy_sheet_to_user(sheet, user):
    sheet.id = None
    sheet.owner = user
    sheet.is_public = False
    sheet.save()
    return sheet

