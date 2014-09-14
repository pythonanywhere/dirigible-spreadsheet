# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import jsonlib
from textwrap import dedent
from uuid import uuid4

from django.db import models, transaction
from django.contrib.auth.models import User

from dirigible.user.models import OneTimePad
from dirigible.sheet.calculate import calculate_with_timeout
from dirigible.sheet.worksheet import (
    Worksheet, worksheet_from_json, worksheet_to_json
)


class Sheet(models.Model):
    last_modified = models.DateTimeField(auto_now=True)

    version = models.IntegerField(default=0)

    owner = models.ForeignKey(User)
    name = models.TextField(default='Untitled')

    width = models.IntegerField(default=52)
    height = models.IntegerField(default=1000)

    contents_json = models.TextField(default=worksheet_to_json(Worksheet()))

    timeout_seconds = models.IntegerField(default=55)

    is_public = models.BooleanField(default=False)
    allow_json_api_access = models.BooleanField(default=False)
    api_key = models.CharField(max_length=72)

    column_widths_json = models.TextField(default='{}')

    usercode = models.TextField(
        default=dedent("""
            load_constants(worksheet)

            # Put code here if it needs to access constants in the spreadsheet
            # and to be accessed by the formulae.  Examples: imports,
            # user-defined functions and classes you want to use in cells.

            evaluate_formulae(worksheet)

            # Put code here if it needs to access the results of the formulae.
        """)
    )


    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.column_widths = jsonlib.loads(self.column_widths_json)
        if not self.api_key:
            self.api_key = str(uuid4())

    def __unicode__(self):
        return 'Sheet %d: %s' % (self.id, self.name)


    def create_private_key(self):
        self.otp = OneTimePad(user=self.owner)
        self.otp.save()
        return unicode(self.otp.guid)


    def _delete_private_key(self):
        self.otp.delete()


    def save(self, *args, **kwargs):
        if self.name == 'Untitled':
            models.Model.save(self, *args, **kwargs) # save to set self.id
            self.name = 'Sheet %d' % (self.id,)
        self.column_widths_json = jsonlib.dumps(self.column_widths)
        models.Model.save(self, *args, **kwargs)


    def unjsonify_worksheet(self):
        return worksheet_from_json(self.contents_json)


    def jsonify_worksheet(self, worksheet):
        self.contents_json = worksheet_to_json(worksheet)


    def merge_non_calc_attrs(self, sheet_in_db):
        self.name = sheet_in_db.name
        self.column_widths = sheet_in_db.column_widths


    def calculate(self):
        private_key = self.create_private_key()
        worksheet = self.unjsonify_worksheet()
        transaction.commit()
        try:
            calculate_with_timeout(worksheet, self.usercode, self.timeout_seconds, private_key)
        finally:
            self._delete_private_key()
        self.jsonify_worksheet(worksheet)


