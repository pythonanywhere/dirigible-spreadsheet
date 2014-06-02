# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django import forms

class ImportCSVForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs['auto_id'] = 'id_import_form_%s'
        forms.Form.__init__(self, *args, **kwargs)
    column = forms.IntegerField(widget=forms.widgets.HiddenInput)
    row = forms.IntegerField(widget=forms.widgets.HiddenInput)
    file = forms.FileField()

