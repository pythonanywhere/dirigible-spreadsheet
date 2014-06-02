# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
from django import forms

from dirigible.test_utils import ResolverTestCase
from dirigible.sheet.forms import ImportCSVForm

class TestImportCSVForm(ResolverTestCase):

    def test_initialisation(self):
        import_form = ImportCSVForm()
        self.assertTrue(all(map(lambda args : isinstance(*args),[
            (import_form.fields['column'], forms.IntegerField),
            (import_form.fields['row'], forms.IntegerField),
            (import_form.fields['file'], forms.FileField)])))


    def test_hidden_fields_appear_with_correct_ids(self):
        import_form = ImportCSVForm()
        autogen_html = import_form.as_p()

        first_hidden_position = autogen_html.find('type="hidden"')
        self.assertFalse(first_hidden_position == -1)
        second_hidden_position = autogen_html.find('type="hidden"', first_hidden_position + 1)
        self.assertFalse(second_hidden_position == -1)
        third_hidden_position = autogen_html.find('type="hidden"', second_hidden_position + 1)
        self.assertEquals(third_hidden_position, -1)

        self.assertTrue('id="id_import_form_column"' in autogen_html)
        self.assertTrue('id="id_import_form_row"' in autogen_html)
        self.assertTrue('id="id_import_form_file"' in autogen_html)
