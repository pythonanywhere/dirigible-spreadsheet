# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from mock import Mock, patch, sentinel
import re
from textwrap import dedent

from django.contrib.auth.models import User

from dirigible.test_utils import ResolverDjangoTestCase

from dirigible.sheet.models import copy_sheet_to_user, Sheet
from dirigible.user.models import OneTimePad
from dirigible.sheet.worksheet import Worksheet, worksheet_to_json



class CopySheetForUserTest(ResolverDjangoTestCase):

    def test_copy_sheet_allows_other_users_to_copy_public_sheets(self):
        user = User(username='Slartibartfast')
        user.save()
        worksheet = Worksheet()
        worksheet.a1.value = 'some-cell-content'
        sheet = Sheet()
        sheet.owner = user
        sheet.is_public = True
        sheet.jsonify_worksheet(worksheet)
        sheet.save()
        original_sheet_id = sheet.id
        other_user = User(username='Othello')
        other_user.save()

        retval = copy_sheet_to_user(sheet, other_user)

        other_user_sheets = Sheet.objects.filter(owner=other_user)
        self.assertEquals(len(other_user_sheets), 1)
        copied_sheet = other_user_sheets[0]
        self.assertFalse(copied_sheet.is_public)
        copied_worksheet = copied_sheet.unjsonify_worksheet()
        self.assertEquals(copied_worksheet.a1.value, 'some-cell-content')
        self.assertEquals(copied_sheet.id, retval.id)
        self.assertNotEquals(retval.id, original_sheet_id)


class SheetModelTest(ResolverDjangoTestCase):

    def test_creation(self):
        user = User(username='sheet_creation')
        sheet = Sheet(owner=user)
        self.assertEquals(sheet.owner, user)
        self.assertEquals(sheet.name, 'Untitled')
        self.assertEquals(sheet.width, 52)
        self.assertEquals(sheet.height, 1000)
        self.assertEquals(sheet.timeout_seconds, 55)
        self.assertEquals(sheet.allow_json_api_access, False)
        self.assertEquals(sheet.is_public, False)
        self.assertEquals(sheet.contents_json, worksheet_to_json(Worksheet()))
        self.assertEquals(sheet.column_widths, {})
        self.assertEquals(
            sheet.usercode,
            dedent("""
                load_constants(worksheet)

                # Put code here if it needs to access constants in the spreadsheet
                # and to be accessed by the formulae.  Examples: imports,
                # user-defined functions and classes you want to use in cells.

                evaluate_formulae(worksheet)

                # Put code here if it needs to access the results of the formulae.
            """)
        )
        self.assertEquals(len(sheet.api_key), 36)
        self.assertIsNotNone(re.match('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', sheet.api_key))


    def test_unicode(self):
        user = User(username='sheet_unicode')
        user.save()
        sheet = Sheet(owner=user, name='the new sheet name')
        sheet.save()
        self.assertEquals(unicode(sheet), 'Sheet %d: %s' % (sheet.id, sheet.name))


    def test_uuid_stays_constant_between_reads(self):
        sheet = Sheet()
        user = User(username='sheet_uuid_constant')
        user.save()
        sheet.owner = user
        sheet.save()
        sheet2 = Sheet.objects.get(pk=sheet.id)
        self.assertEquals(sheet.api_key, sheet2.api_key)


    def test_create_private_key_uses_onetimepad(self):
        sheet = Sheet()
        sheet.version = 155
        user = User(username='HashBrown')
        user.set_password('glurk')
        user.save()
        sheet.owner = user
        self.assertEquals(len(OneTimePad.objects.all()), 0)
        self.assertEquals(
            sheet.create_private_key(),
            OneTimePad.objects.get(user=sheet.owner).guid)
        sheet._delete_private_key()


    def test_delete_private_key_does(self):
        self.assertEquals(len(OneTimePad.objects.all()), 0)
        sheet = Sheet()
        user = User(username='fred')
        user.save()
        sheet.owner = user
        sheet.create_private_key()
        self.assertEquals(len(OneTimePad.objects.all()), 1)
        sheet._delete_private_key()
        self.assertEquals(len(OneTimePad.objects.all()), 0)


    @patch('dirigible.sheet.sheet.worksheet_from_json')
    def test_unjsonify_worksheet_should_return_worksheet(self, mock_worksheet_from_json):
        sheet = Sheet()
        sheet.contents_json = sentinel.contents_json

        worksheet = sheet.unjsonify_worksheet()

        self.assertEquals(worksheet, mock_worksheet_from_json.return_value)
        self.assertCalledOnce(mock_worksheet_from_json, sentinel.contents_json)


    @patch('dirigible.sheet.sheet.worksheet_to_json')
    def test_jsonify_worksheet_should_write_json_to_contents_json_field(self, mock_worksheet_to_json):
        sheet = Sheet()

        sheet.jsonify_worksheet(sentinel.worksheet)

        self.assertCalledOnce(mock_worksheet_to_json, sentinel.worksheet)
        self.assertEquals(sheet.contents_json, mock_worksheet_to_json.return_value)


    @patch('dirigible.sheet.sheet.jsonlib')
    def test_roundtrip_column_widths_to_db(self, mock_jsonlib):
        COLUMN_WIDTHS = {'1': 11, '2': 22, '3': 33}
        mock_jsonlib.loads.return_value = COLUMN_WIDTHS
        mock_jsonlib.dumps.return_value = sentinel.json
        user = User(username='sheet_roundtrip_column_widths')
        user.save()
        sheet = Sheet(owner=user)
        DEFAULT_COLUMN_WIDTHS_JSON = '{}'
        self.assertEquals(
            mock_jsonlib.loads.call_args,
            ((DEFAULT_COLUMN_WIDTHS_JSON,), {})
        )
        sheet.column_widths = COLUMN_WIDTHS

        sheet.save()
        self.assertEqual(
            mock_jsonlib.dumps.call_args,
            ((COLUMN_WIDTHS,), {})
        )
        pk = sheet.id

        sheet2 = Sheet.objects.get(pk=pk)
        self.assertEquals(sheet2.column_widths, COLUMN_WIDTHS)


    def test_sheet_name_set_on_save_if_name_is_default(self):
        user = User(username='sheet_name_default')
        user.save()
        sheet = Sheet(owner=user)
        sheet.save()
        self.assertEquals(sheet.name, 'Sheet %d' % (sheet.id,))


    def test_sheet_name_not_set_on_save_if_name_is_not_default(self):
        user = User(username='sheet_name_non_default')
        user.save()
        sheet = Sheet(owner=user)
        sheet.name = 'new sheet name'
        sheet.save()
        self.assertEquals(sheet.name, 'new sheet name')


    def test_last_modified(self):
        last_modified_field = Sheet._meta.get_field_by_name('last_modified')[0]
        self.assertEquals(last_modified_field.auto_now, True)


    def test_version_default(self):
        version_field = Sheet._meta.get_field_by_name('version')[0]
        self.assertEquals(version_field.default, 0)


    def test_merge_non_calc_attrs_should_copy_some_attrs(self):
        s1 = Sheet()
        s1.name = 's1'
        s1.column_widths = {'s1': 0}
        s1.contents_json = sentinel.sheet1
        s2 = Sheet()
        s2.name = 's2'
        s2.column_widths = {'s2': 0}
        s2.contents_json = sentinel.sheet2

        s1.merge_non_calc_attrs(s2)

        self.assertEquals(s1.name, 's2')
        self.assertEquals(s1.column_widths, {'s2': 0})
        self.assertEquals(s1.contents_json, sentinel.sheet1)


    @patch('dirigible.sheet.sheet.calculate_with_timeout')
    def test_calculate_calls_calculate_with_unjsonified_worksheet_and_saves_recalced_json(
        self, mock_calculate
    ):
        sheet = Sheet()
        sheet.jsonify_worksheet = Mock()
        sheet.unjsonify_worksheet = Mock()
        sheet.usercode = sentinel.usercode
        sheet.timeout_seconds = sentinel.timeout_seconds
        sheet.create_private_key = Mock()
        sheet.otp = Mock()

        sheet.calculate()

        self.assertCalledOnce(
            mock_calculate,
            sheet.unjsonify_worksheet.return_value,
            sheet.usercode,
            sheet.timeout_seconds,
            sheet.create_private_key.return_value
        )
        self.assertCalledOnce(sheet.jsonify_worksheet, sheet.unjsonify_worksheet.return_value)


    @patch('dirigible.sheet.sheet.calculate_with_timeout')
    def test_calculate_always_deletes_private_key_in_finally_block(
        self, mock_calculate
    ):
        def raiser(*a, **kw):
            raise Exception()
        mock_calculate.side_effect = raiser
        sheet = Sheet()
        user = User(username='geoff')
        user.save()
        sheet.owner = user
        sheet._delete_private_key = Mock()

        self.assertRaises(Exception, sheet.calculate)

        self.assertCalledOnce(sheet._delete_private_key)
