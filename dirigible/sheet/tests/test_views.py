# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from cgi import parse_qs
from mock import Mock, patch, sentinel
import re
from StringIO import StringIO
from urlparse import urlparse

import django
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import (
    Http404, HttpRequest, HttpResponse, HttpResponseForbidden,
    HttpResponseRedirect
)
from django.shortcuts import render
from django.test.testcases import disable_transaction_methods, restore_transaction_methods, TransactionTestCase

from dirigible.test_utils import (
    assert_security_classes_exist, die, ResolverTestCase
)

from sheet.cell import Cell, undefined
from sheet.forms import ImportCSVForm
from sheet.models import Clipboard, Sheet
from sheet.views import (
    calculate, clear_cells, clipboard, copy_sheet, export_csv, get_json_grid_data_for_ui,
    get_json_meta_data_for_ui, import_csv, import_xls, page, set_cell_formula,
    set_column_widths, set_sheet_name, set_sheet_security_settings,
    set_sheet_usercode, update_sheet_with_version_check
)
from sheet.worksheet import Worksheet, worksheet_from_json
from sheet.importer import DirigibleImportError

class SheetViewTestCase(TransactionTestCase, ResolverTestCase):
    maxDiff = None

    def assertMockUpdaterCalledOnceWithWorksheet(
        self, mock_update_sheet_with_version_check, sheet,
        expected_worksheet
    ):
        self.assertEquals(
            len(mock_update_sheet_with_version_check.call_args_list),
            1
        )
        if mock_update_sheet_with_version_check.call_args_list == []:
            self.fail('Not called')
        args, kwargs = mock_update_sheet_with_version_check.call_args_list[0]
        self.assertEquals(args, (sheet, ))
        self.assertTrue('contents_json' in kwargs)
        resulting_worksheet = worksheet_from_json(kwargs['contents_json'])
        self.assertEquals(resulting_worksheet, expected_worksheet)



def set_up_view_test(self):
    self.user = User(username='sheetviewtestuser')
    self.user.save()
    self.sheet = Sheet(owner=self.user)
    self.sheet.save()
    self.request = HttpRequest()
    self.request.user = self.user


def create_view_security_test(
    class_name, view, get_dict=None, post_dict=None, files_dict=None, extra_view_args=None
):
    if extra_view_args is None:
        extra_view_args = []

    class _ViewSecurityTest(SheetViewTestCase):

        setUp = set_up_view_test

        def test_view_login_required(self):
            request = HttpRequest()
            request.user = AnonymousUser()
            request.META['SERVER_NAME'] = 'servername'
            request.META['SERVER_PORT'] = '80'
            actual = view(
                request, self.user.username, self.sheet.id, *extra_view_args
            )
            self.assertTrue(isinstance(actual, HttpResponseRedirect))

            redirect_url = urlparse(actual['Location'])
            self.assertEquals(redirect_url.path, settings.LOGIN_URL)


        def test_view_should_raise_on_bad_sheet(self):
            self.assertRaises(Http404, view, self.request, self.user.username, 1234, *extra_view_args)


        def test_view_should_raise_404_if_param_user_not_sheet_user(self):
            wrong_user = User(username='validbutnotowner')
            wrong_user.save()
            self.assertRaises(Http404, view, self.request, wrong_user.username, self.sheet.id, *extra_view_args)


        def test_view_should_raise_if_nonexistent_user_in_params(self):
            self.assertRaises(Http404, view, self.request, 'baduser', self.sheet.id, *extra_view_args)


        def test_view_should_return_403_with_template_if_non_admin_request_user_doesnt_match_sheet_owner(self):
            sheet_owner = User(username='sheetowner')
            request = HttpRequest()
            request.user = sheet_owner
            response = view(
                request, self.user.username, self.sheet.id, *extra_view_args)
            self.assertEquals(type(response), HttpResponseForbidden)
            expected_content = django.template.loader.render_to_string("403.html")
            self.assertEquals(response.content, expected_content)


        def test_view_should_allow_admin_user(self):
            admin_user = User(username='validadminuser')
            admin_user.is_staff = True
            admin_user.save()
            if post_dict is not None:
                self.request.POST = post_dict
            if get_dict is not None:
                self.request.GET = get_dict
            self.request.FILES = files_dict
            self.request.user = admin_user

            response = view(self.request, self.user.username, self.sheet.id, *extra_view_args)

            if type(response) == HttpResponseRedirect:
                redirect_url = urlparse(response['Location'])
                self.assertNotEquals(redirect_url.path, settings.LOGIN_URL)
            else:
                self.assertEqual(type(response), HttpResponse)


    return type(class_name, (_ViewSecurityTest,), {})


class ImportXLSSecurityTest(SheetViewTestCase):
    post_args = {"column": "1", "row": "1"}, {'file': 'file'}
    view = import_xls
    setUp = set_up_view_test

    def test_view_login_required(self):
        request = HttpRequest()
        request.user = AnonymousUser()
        request.META['SERVER_NAME'] = 'servername'
        request.META['SERVER_PORT'] = '80'
        actual = import_xls(request, self.user.username)

        self.assertTrue(isinstance(actual, HttpResponseRedirect))

        redirect_url = urlparse(actual['Location'])
        self.assertEquals(redirect_url.path, settings.LOGIN_URL)


    def test_cannot_upload_to_another_users_dashboard(self):
        other_user = User(username='dont mess with my dashboard')
        other_user.save()

        response = import_xls(self.request, other_user.username)

        self.assertEquals(type(response), HttpResponseForbidden)
        expected_content = django.template.loader.render_to_string("403.html")
        self.assertEquals(response.content, expected_content)


class ImportXLSTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.mkstemp')
    @patch('sheet.views.os')
    @patch('sheet.views.xlrd')
    def test_import_xls_creates_sheets_for_non_empty_worksheets_using_tempfiles(
            self, mock_xlrd, mock_os, mock_mkstemp
    ):
        def make_sheet(name, cols, rows):
            sheet = Mock()
            sheet.name = name
            sheet.ncols = cols
            sheet.nrows = rows
            mock_cell = Mock()
            mock_cell.value = 'cell value'
            sheet.cell.return_value = mock_cell
            return sheet
        data = [
            ('first_imported_sheet', 2, 3),
            ('2nd imported sheet', 2, 3),
            ('zero rows', 2, 0),
            ('zero cols', 0, 3),
        ]
        sheets = [make_sheet(*datum) for datum in data]

        mock_workbook = Mock()
        mock_workbook.sheets.return_value = sheets
        mock_xlrd.open_workbook.return_value = mock_workbook
        mock_mkstemp.return_value = (sentinel.handle, sentinel.filename)
        mock_file = Mock()
        mock_file.name = 'uploaded file.xls'
        mock_file.read.return_value = sentinel.contents

        self.request.FILES = {}
        self.request.FILES['file'] = mock_file

        response = import_xls(self.request, self.user.username)

        self.assertTrue(isinstance(response, HttpResponseRedirect))

        self.assertCalledOnce(mock_os.write, sentinel.handle, sentinel.contents)
        self.assertCalledOnce(mock_xlrd.open_workbook, sentinel.filename)

        actual_sheets = Sheet.objects.all()
        actual_sheetnames = [sheet.name for sheet in actual_sheets]
        self.assertTrue('uploaded file - %s' % (sheets[0].name,) in actual_sheetnames)
        self.assertTrue('uploaded file - %s' % (sheets[1].name,) in actual_sheetnames)
        self.assertFalse('uploaded file - %s' % (sheets[2].name,) in actual_sheetnames)
        self.assertFalse('uploaded file - %s' % (sheets[3].name,) in actual_sheetnames)

        self.assertCalledOnce(mock_os.close, sentinel.handle)
        self.assertCalledOnce(mock_os.unlink, sentinel.filename)


    @patch('sheet.views.mkstemp')
    @patch('sheet.views.os')
    def test_import_xls_closes_and_deletes_tempfile(self, mock_os, mock_mkstemp):
        mock_mkstemp.return_value = (sentinel.handle, sentinel.filename)
        mock_file = Mock()

        def die(*_):
            raise Exception('urk')
        mock_os.write.side_effect = die

        self.request.FILES = {}
        self.request.FILES['file'] = mock_file

        response = import_xls(self.request, self.user.username)

        self.assertCalledOnce(mock_os.close, sentinel.handle)
        self.assertCalledOnce(mock_os.unlink, sentinel.filename)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(
            response.content,
            render(
                self.request,
                'import_xls_error.html',
                {},
            ).content
        )


    @patch('sheet.views.xlrd')
    @patch('sheet.views.os')
    @patch('sheet.views.worksheet_from_excel')
    def test_import_xls_imports_values_and_calls_calculate_on_each_sheet(
        self, mock_worksheet_from_excel, mock_os, mock_xlrd
    ):
        mock_xl_sheet1 = Mock()
        mock_xl_sheet1.name = 'xl sheet 1'
        mock_xl_sheet1.ncols = 3
        mock_xl_sheet1.nrows = 4
        mock_xl_sheet2 = Mock()
        mock_xl_sheet2.name = 'xl sheet 2'
        mock_xl_sheet2.ncols = 3
        mock_xl_sheet2.nrows = 4
        mock_workbook = Mock()
        mock_workbook.sheets.return_value = [mock_xl_sheet1, mock_xl_sheet2]
        mock_xlrd.open_workbook.return_value = mock_workbook

        expected_ws1 = Worksheet()
        expected_ws1.name = 'ws1'
        expected_ws1.A1.formula = 'xl sheet 1'
        expected_ws2 = Worksheet()
        expected_ws2.name = 'ws2'
        expected_ws2.A1.formula = 'xl sheet 2'
        sheets = [expected_ws1, expected_ws2]
        mock_worksheet_from_excel.side_effect = lambda _: sheets.pop(0)

        self.request.FILES = {}
        self.request.FILES['file'] = Mock()

        response = import_xls(self.request, self.user.username)

        self.assertEquals(
            mock_worksheet_from_excel.call_args_list,
            [
                ((mock_xl_sheet1,), {}),
                ((mock_xl_sheet2,), {}),
            ]
        )

        actual_sheet1 = Sheet.objects.get(name__icontains=mock_xl_sheet1.name)
        actual_sheet2 = Sheet.objects.get(name__icontains=mock_xl_sheet2.name)

        actual_ws1 = actual_sheet1.unjsonify_worksheet()
        actual_ws2 = actual_sheet2.unjsonify_worksheet()

        self.assertEquals( actual_ws1.A1.formula, 'xl sheet 1')
        self.assertEquals( actual_ws1.A1.formatted_value, 'xl sheet 1')
        self.assertEquals(
            actual_ws1.A1.formatted_value,
            'xl sheet 1',
            'possibly failed because recalc not done'
        )

        self.assertEquals( actual_ws2.A1.formula, 'xl sheet 2')
        self.assertEquals( actual_ws2.A1.formatted_value, 'xl sheet 2')
        self.assertEquals(
            actual_ws2.A1.formatted_value,
            'xl sheet 2',
            'possibly failed because recalc not done'
        )

        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertEquals(response['Location'], '/')


    @patch('sheet.views.calculate', die())
    @patch('sheet.views.xlrd')
    @patch('sheet.views.os')
    @patch('sheet.views.worksheet_from_excel')
    def test_import_xls_reports_success_on_exception_from_calculate(
        self, mock_worksheet_from_excel, mock_os, mock_xlrd
    ):
        mock_xl_sheet1 = Mock()
        mock_xl_sheet1.name = 'xl sheet 1'
        mock_xl_sheet1.ncols = 3
        mock_xl_sheet1.nrows = 4
        mock_workbook = Mock()
        mock_workbook.sheets.return_value = [mock_xl_sheet1]
        mock_xlrd.open_workbook.return_value = mock_workbook

        expected_ws1 = Worksheet()
        expected_ws1.name = 'ws1'
        expected_ws1.A1.formula = 'xl sheet 1'
        sheets = [expected_ws1]
        mock_worksheet_from_excel.side_effect = lambda _: sheets.pop(0)

        self.request.FILES = {}
        self.request.FILES['file'] = Mock()

        response = import_xls(self.request, self.user.username)

        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertEquals(response['Location'], '/')



TEST_SIMPLE_CSV = '''1,2,3'''

TEST_EVIL_CSV_WITH_BLANKROW_SPACES_AND_DIFFERENT_LENGTH_ROWS = '''
1,2,3
a, b,c,d
=10,=20,=30'''

ImportCSVSecurityTest = create_view_security_test(
    "ImportCSVSecurityTest", import_csv,
    post_dict={"column": "1", "row": "1"},
    files_dict={'file': 'file'}
)

class ImportCSVTest(SheetViewTestCase):

    setUp = set_up_view_test


    @patch('sheet.views.update_sheet_with_version_check')
    def test_import_csv_should_import_csv_and_update_sheet_with_version_check(
        self, mock_update_sheet_with_version_check
    ):
        worksheet = Worksheet()
        for column in range(2, 7):
            for row in range(3, 9):
                worksheet[(column, row)].formula = 'old'
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()

        test_csv_file = StringIO(TEST_EVIL_CSV_WITH_BLANKROW_SPACES_AND_DIFFERENT_LENGTH_ROWS)
        test_csv_file.name = 'filename'
        test_csv_file.size = 10

        self.request.FILES['file'] = test_csv_file
        self.request.POST['column'] = 3
        self.request.POST['csv_encoding'] = 'excel'
        self.request.POST['row'] = 4

        mock_update_sheet_with_version_check.return_value = True
        response = import_csv(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertEquals(response['Location'], '/user/sheetviewtestuser/sheet/%d/' % (self.sheet.id, ))

        expected = [
            # outside top left corner unchanged
            ((2, 4), 'old'),
            ((3, 3), 'old'),

            # outside bottom right corner unchanged
            ((6, 7), 'old'),
            ((5, 8), 'old'),

            # inside the imported area
            ((3, 4), 'old'), #blank row in csv has no effect
            ((4, 4), 'old'),
            ((5, 4), 'old'),
            ((3, 5), '1'),
            ((4, 5), '2'),
            ((5, 5), '3'),
            ((3, 6), 'a'),
            ((4, 6), ' b'),
            ((5, 6), 'c'),
            ((6, 6), 'd'),
            ((3, 7), '=10'),
            ((4, 7), '=20'),
            ((5, 7), '=30'),
        ]
        (call_args, call_kwargs) = mock_update_sheet_with_version_check.call_args_list[0]
        self.assertEquals(call_args, (self.sheet,))
        self.assertEquals(call_kwargs.keys(), ['contents_json'])
        resulting_worksheet = worksheet_from_json(call_kwargs['contents_json'])
        for location, value in expected:
            self.assertEquals(
                resulting_worksheet[location].formula, value,
                'location %s: %s != %s' % (location, resulting_worksheet[location].formula, value)
            )


    @patch('sheet.views.ImportCSVForm')
    def test_import_csv_handles_null_file(self, mock_import_csv_form):
        mock_import_csv_form.side_effect = lambda *args, **kwargs: ImportCSVForm(*args, **kwargs)

        self.request.POST['column'] = 3
        self.request.POST['row'] = 4
        self.request.POST['csv_encoding'] = 'excel'
        self.request.FILES = {}

        response = import_csv(self.request, self.user.username, self.sheet.id)

        self.assertEquals(
            mock_import_csv_form.call_args_list,
            [((self.request.POST, self.request.FILES), {})]
        )

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertTrue('not in a recognised CSV format' in response.content)


    @patch('sheet.views.worksheet_from_csv')
    @patch('sheet.views.get_object_or_404')
    def test_view_uses_and_handles_errors_from_worksheet_from_csv(
            self, mock_get_object_or_404, mock_worksheet_from_csv
    ):
        def raiser(*args, **kwargs):
            raise DirigibleImportError('foo')
        mock_worksheet_from_csv.side_effect = raiser

        self.request.POST['column'] = 3
        self.request.POST['row'] = 4
        mock_file = Mock()
        mock_file.readlines = lambda : []
        self.request.FILES = {'file': mock_file}

        mock_sheet = Sheet(owner=self.user)
        mock_sheet.save()
        mock_worksheet = Mock()
        mock_sheet.unjsonify_worksheet = lambda : mock_worksheet
        mock_get_object_or_404.return_value = mock_sheet

        for csv_encoding in ['excel', 'other']:
            self.request.POST['csv_encoding'] = csv_encoding

            response = import_csv(self.request, self.user.username, self.sheet.id)

            self.assertCalledOnce(mock_worksheet_from_csv,
                    mock_worksheet, mock_file, 3, 4, csv_encoding=='excel'
            )
            self.assertTrue(isinstance(response, HttpResponse))
            self.assertTrue('not in a recognised CSV format' in response.content)
            mock_worksheet_from_csv.reset_mock()


    @patch('sheet.views.worksheet_from_csv')
    @patch('sheet.views.calculate')
    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_calls_calculate_view_after_update_sheet(
        self, mock_update_sheet_with_version_check, mock_calculate,
        mock_worksheet_from_csv
    ):
        self.request.POST['column'] = 3
        self.request.POST['row'] = 4
        self.request.POST['csv_encoding'] = 'excel'
        mock_file = Mock()
        mock_file.readlines = lambda : []
        self.request.FILES = {'file': mock_file}
        mock_worksheet_from_csv.return_value = Worksheet()
        mock_update_sheet_with_version_check.return_value = True
        import_csv(self.request, self.user.username, self.sheet.id)

        self.assertCalledOnce(
            mock_calculate,
            self.request, self.sheet.owner.username, self.sheet.id,
        )



ExportCSVSecurityTest = create_view_security_test(
    "ExportCSVSecurityTest",
    export_csv,
    extra_view_args = ['excel']
)

class ExportCSVTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.get_object_or_404')
    @patch('sheet.views.worksheet_to_csv')
    def test_export_excel_csv_should_produce_csv_with_correct_http_headers_and_content(
        self, mock_worksheet_to_csv, mock_get_object
    ):
        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        mock_sheet.name = "Algernon"
        expected_filename = "%s.csv" % (mock_sheet.name,)

        expected_content = "Hello world"
        mock_worksheet_to_csv.return_value = expected_content

        response = export_csv(self.request, self.user.username, self.sheet.id, 'excel')

        self.assertCalledOnce(
                mock_worksheet_to_csv,
                mock_sheet.unjsonify_worksheet.return_value, encoding='windows-1252'
        )

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/csv')
        self.assertEquals(response['Content-Disposition'], 'attachment; filename=%s' % (expected_filename,))
        self.assertEquals(response['Content-Length'], str(len(expected_content)))

        self.assertEquals(response.content, expected_content)


    @patch('sheet.views.get_object_or_404')
    @patch('sheet.views.worksheet_to_csv')
    def test_export_unicode_csv_should_produce_csv_with_correct_http_headers_and_content(
        self, mock_worksheet_to_csv, mock_get_object
    ):
        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        mock_sheet.name = "Algernon"
        expected_filename = "%s.csv" % (mock_sheet.name,)

        expected_content = "Hello world"
        mock_worksheet_to_csv.return_value = expected_content

        response = export_csv(self.request, self.user.username, self.sheet.id, 'unicode')

        self.assertCalledOnce(
                mock_worksheet_to_csv,
                mock_sheet.unjsonify_worksheet.return_value, encoding='utf-8'
        )


        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/csv')
        self.assertEquals(response['Content-Disposition'], 'attachment; filename=%s' % (expected_filename,))
        self.assertEquals(response['Content-Length'], str(len(expected_content)))

        self.assertEquals(response.content, expected_content)


    def test_export_excel_csv_handles_encoding_error_and_returns_message(self):
        some_kanji = u'\u30bc\u30ed\u30a6\u30a3\u30f3\u30b0'
        worksheet = Worksheet()
        worksheet.a1.value = some_kanji
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()

        response = export_csv(self.request, self.user.username, self.sheet.id, 'excel')

        self.assertEquals(response.status_code, 200)

        self.assertTrue('Could not export' in response.content)


    def test_export_csv_allows_other_users_to_view_public_sheets(self):
        self.sheet.is_public = True
        worksheet = Worksheet()
        worksheet.a1.value = 'some-cell-content'
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()
        other_user = User(username='Othello')
        other_user.save()
        self.request.user = other_user

        response = export_csv(self.request, self.user.username, self.sheet.id, 'excel')

        self.assertEquals(response.status_code, 200)
        self.assertTrue('some-cell-content' in response.content)


    def test_export_csv_allows_anonymous_user_to_view_public_sheets(self):
        self.sheet.is_public = True
        worksheet = Worksheet()
        worksheet.a1.value = 'some-cell-content'
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()
        self.request.user = AnonymousUser()
        self.request.META['SERVER_NAME'] = 'servername'
        self.request.META['SERVER_PORT'] = '80'

        response = export_csv(self.request, self.user.username, self.sheet.id, 'excel')

        self.assertEquals(response.status_code, 200)
        self.assertTrue('some-cell-content' in response.content)



CopySheetSecurityTest = create_view_security_test(
    "CopySheetSecurityTest",
    copy_sheet
)

class CopySheetTest(SheetViewTestCase):

    setUp = set_up_view_test

    def test_copy_sheet_allows_other_users_to_copy_public_sheets(self):
        self.sheet.is_public = True
        worksheet = Worksheet()
        worksheet.a1.value = 'some-cell-content'
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()
        other_user = User(username='Othello')
        other_user.save()
        self.request.user = other_user

        response = copy_sheet(self.request, self.user.username, self.sheet.id)

        other_user_sheets = Sheet.objects.filter(owner=other_user)
        self.assertEquals(len(other_user_sheets), 1)
        copied_sheet = other_user_sheets[0]
        self.assertFalse(copied_sheet.is_public)
        copied_worksheet = copied_sheet.unjsonify_worksheet()
        self.assertEquals(copied_worksheet.a1.value, 'some-cell-content')

        self.assertTrue(isinstance(response, HttpResponseRedirect))

        redirect_url = urlparse(response['Location'])
        self.assertEquals(
            redirect_url.path,
            reverse(
                'sheet_page',
                kwargs={
                    'username': other_user.username,
                    'sheet_id': copied_sheet.id,
                }
            )
        )


    def test_copy_sheet_requires_login_for_anonymous_user(self):
        self.sheet.is_public = True
        worksheet = Worksheet()
        worksheet.a1.value = 'some-cell-content'
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()
        self.request.user = AnonymousUser()
        self.request.META['SERVER_NAME'] = 'servername'
        self.request.META['SERVER_PORT'] = '80'
        self.request.get_full_path = lambda: 'request-path'

        response = copy_sheet(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponseRedirect))

        redirect_url = urlparse(response['Location'])
        self.assertEquals(redirect_url.path, settings.LOGIN_URL)
        redirect_query_params = parse_qs(redirect_url.query)
        self.assertEquals(redirect_query_params['next'], ['request-path'])




PageViewSecurityTest = create_view_security_test("PageViewSecurityTest", page)

class PageViewTest(SheetViewTestCase):

    setUp = set_up_view_test

    def test_page_should_return_response_for_logged_in_owner(self):
        response = page(self.request, self.user.username, self.sheet.id)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(response.status_code, 200)


    @patch('sheet.views.render')
    @patch('sheet.views.get_object_or_404')
    @patch('sheet.views.ImportCSVForm')
    def test_page_should_render_template_with_correct_stuff_before_setting_userprofile_flag(
        self, mock_import_csv_form, mock_get_object_or_404, mock_render
    ):
        mock_get_object_or_404.return_value = self.sheet

        def check_userprofile_flag_not_set(*args, **kwargs):
            self.assertEquals(
                self.user.get_profile().has_seen_sheet_page,
                False,
                'user profile has_seen_sheet_page set to True before first render'
            )
            return sentinel.response
        mock_render.side_effect = check_userprofile_flag_not_set

        actual = page(self.request, self.user.username, self.sheet.id)

        self.assertCalledOnce(
            mock_render,
            self.request,
            'sheet_page.html',
            {
                'sheet': self.sheet,
                'user': self.user,
                'profile': self.user.get_profile(),
                'import_form': mock_import_csv_form.return_value,
            }
        )
        self.assertEquals(actual, sentinel.response)
        self.assertTrue(self.user.get_profile().has_seen_sheet_page)


    @patch('sheet.views.Context')
    @patch('sheet.views.get_template')
    @patch('sheet.views.send_mail')
    def test_view_should_send_welcome_email_if_new_user(
            self, mock_send_mail, mock_get_template, mock_Context
    ):
        page(self.request, self.user.username, self.sheet.id)

        self.assertCalledOnce(mock_get_template, 'welcome_email.txt')
        self.assertCalledOnce(mock_Context, dict(user=self.user))
        self.assertCalledOnce(
            mock_get_template.return_value.render,
            mock_Context.return_value
        )
        self.assertCalledOnce(
            mock_send_mail,
            'Welcome to Dirigible',
            mock_get_template.return_value.render.return_value,
            '',
            [self.user.email],
            fail_silently=True
        )


    @patch('sheet.views.render')
    def test_page_allows_other_users_to_view_public_sheets(self, mock_render):
        mock_render.side_effect = render
        self.sheet.is_public = True
        self.sheet.save()
        other_user = User(username='Othello')
        other_user.save()
        self.request.user = other_user

        response = page(self.request, self.user.username, self.sheet.id)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('id_usercode' in response.content)
        (request, template_name, context), kwargs = mock_render.call_args

        self.assertTrue(context['sheet'].public_view_mode)


    @patch('sheet.views.render')
    def test_page_allows_anonymous_user_to_view_public_sheets(self, mock_render):
        mock_render.side_effect = render
        self.sheet.is_public = True
        self.sheet.save()
        self.request.user = AnonymousUser()
        self.request.META['SERVER_NAME'] = 'servername'
        self.request.META['SERVER_PORT'] = '80'

        response = page(self.request, self.user.username, self.sheet.id)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('id_usercode' in response.content)
        (request, template_name, context), kwargs = mock_render.call_args
        self.assertTrue(context['sheet'].public_view_mode)


SetCellFormulaSecurityTest = create_view_security_test(
    "SetCellFormulaSecurityTest", set_cell_formula,
    post_dict={"column": "1", "row": "1", "formula": "woo"}
)

class SetCellFormulaTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_should_set_cell_formula_and_update_sheet_with_version_check(
        self, mock_update_sheet_with_version_check
    ):
        original_worksheet = Worksheet()
        original_worksheet[23, 89].formula = "old formula"
        original_worksheet[23, 90].formula = "formula that should remain untouched"
        self.sheet.jsonify_worksheet(original_worksheet)
        self.sheet.save()

        expected_column = 23
        expected_row = 89
        expected_formula = 'new formula'
        self.request.POST["column"] = str(expected_column)
        self.request.POST["row"] = str(expected_row)
        self.request.POST["formula"] = expected_formula
        mock_update_sheet_with_version_check.return_value = True

        response = set_cell_formula(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(response.content, "OK")

        ((call_args, call_kwargs),) = mock_update_sheet_with_version_check.call_args_list
        self.assertEquals(call_args, (self.sheet,))
        self.assertEquals(call_kwargs.keys(), ['contents_json'])
        resulting_worksheet = worksheet_from_json(call_kwargs['contents_json'])
        self.assertEquals(resulting_worksheet[23, 89].formula, 'new formula')
        self.assertEquals(resulting_worksheet[23, 90].formula, "formula that should remain untouched")


    def test_other_users_cant_scf_even_on_public_worksheets(self):
        self.sheet.is_public = True
        self.sheet.save()
        other_user = User(username='Othello')
        other_user.save()
        self.request.user = other_user

        expected_formula = 'new formula'
        self.request.POST["column"] = '1'
        self.request.POST["row"] = '1'
        self.request.POST["formula"] = expected_formula

        response = set_cell_formula(self.request, self.user.username, self.sheet.id)
        self.assertEquals(response.status_code, 403)

        resulting_sheet = Sheet.objects.get(pk=self.sheet.id)
        resulting_worksheet = resulting_sheet.unjsonify_worksheet()
        self.assertEquals(resulting_worksheet.a1.formula, None)



ClearCellsSecurityTest = create_view_security_test(
    "ClearCellsSecurityTest",
    clear_cells,
    post_dict = {'range': '2,1,3,3'},
)


class ClearCellsTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_should_clear_range_given_and_update_sheet_with_version_check(
        self, mock_update_sheet_with_version_check
    ):
        mock_update_sheet_with_version_check.return_value = True

        worksheet = Worksheet()
        worksheet.B1.formula = 'be one'
        worksheet.B2.formula = 'bee to'
        worksheet.B3.formula = 'be free'
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()

        self.request.POST = {'range': '2,1,2,2'}

        clear_cells(self.request, self.user.username, self.sheet.id)

        expected_worksheet = Worksheet()
        expected_worksheet.B1.formula = None
        expected_worksheet.B2.formula = None
        expected_worksheet.B3.formula = 'be free'

        self.assertMockUpdaterCalledOnceWithWorksheet(
            mock_update_sheet_with_version_check,
            self.sheet,
            expected_worksheet
        )


    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_should_return_ok_if_successful(
        self, mock_update_sheet_with_version_check
    ):
        mock_update_sheet_with_version_check.return_value = True

        self.request.POST = {'range': '2,1,3,2'}

        response = clear_cells(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(response.content, "OK")


    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_should_return_fail_if_update_fails(
        self, mock_update_sheet_with_version_check
    ):
        mock_update_sheet_with_version_check.return_value = False

        self.request.POST = {'range': '2,1,3,2'}

        response = clear_cells(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(response.content, "FAILED")



SetSheetUsercodeSecurityTest = create_view_security_test(
    "SetSheetUsercodeSecurityTest", set_sheet_usercode,
    post_dict={ 'usercode' : '' }
)

class SetSheetUsercodeTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_should_set_sheet_usercode_and_updates_version(self, mock_update_sheet_with_version_check):
        expected_usercode = 'mary had a leg of lamb'
        self.request.POST["usercode"] = str(expected_usercode)
        mock_update_sheet_with_version_check.return_value = True

        response = set_sheet_usercode(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(response.content, "OK")

        ((call_args, call_kwargs),) = mock_update_sheet_with_version_check.call_args_list
        self.assertEquals(call_args, (self.sheet,))
        self.assertEquals(call_kwargs, {'usercode': expected_usercode})


    def test_view_set_sheet_usercode_fixes_windows_line_endings(self):
        submitted_usercode = 'mary had a\r\n leg of\r lamb'
        expected_usercode = 'mary had a\n leg of\r lamb'
        self.request.POST["usercode"] = str(submitted_usercode)

        set_sheet_usercode(self.request, self.user.username, self.sheet.id)

        sheet_from_db = Sheet.objects.get(pk=self.sheet.id)
        self.assertEquals(
            sheet_from_db.usercode,
            expected_usercode
        )


SetSheetSecuritySettingsSecurityTest = create_view_security_test(
    "SetSheetSecuritySettingsSecurityTest", set_sheet_security_settings,
    post_dict={
        "is_public": "false",
        "api_key": "this_is_the_api_key",
        "allow_json_api_access": "true"
    }
)

class SetSheetSecuritySettingsTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.get_object_or_404')
    def test_view_should_set_sheet_security_settings(self, mock_get_object):
        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        mock_sheet.api_key = 'old_api_key'
        mock_sheet.allow_json_api_access = False
        mock_sheet.is_public = False

        self.request.POST["api_key"] = 'new_api_key'
        self.request.POST["allow_json_api_access"] = 'true'
        self.request.POST["is_public"] = 'true'

        def save_sheet():
            self.assertEquals(mock_sheet.api_key, 'new_api_key',
                              'sheet api_key not set before save')
            self.assertEquals(mock_sheet.allow_json_api_access, True,
                              'sheet json api access not set before save')
            self.assertEquals(mock_sheet.is_public, True,
                              'sheet public access not set before save')
        mock_sheet.save.side_effect = save_sheet

        actual = set_sheet_security_settings(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content, 'OK')

        self.assertEquals(
            mock_get_object.call_args,
            ((Sheet,), dict(pk=self.sheet.id, owner__username=self.user.username))
        )

        self.assertEquals(
            mock_sheet.method_calls,
            [('save', (), {}), ]
        )



SetSheetNameSecurityTest = create_view_security_test(
    "SetSheetNameSecurityTest", set_sheet_name,
    post_dict={"new_value": "New name"}
)

class SetSheetNameTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.get_object_or_404')
    def test_view_should_set_sheet_name(self, mock_get_object):
        expected_sheet_name = 'mary had a leg of lamb'
        self.request.POST["new_value"] = expected_sheet_name

        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        def save_sheet():
            self.assertEquals(mock_sheet.name, expected_sheet_name,
                              'sheet name not set before save')
        mock_sheet.save.side_effect = save_sheet

        actual = set_sheet_name(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content,
            '{"is_error":false, "html":"%s"}' % (expected_sheet_name,))

        self.assertEquals(
            mock_get_object.call_args,
            ((Sheet,), dict(pk=self.sheet.id, owner__username=self.user.username))
        )

        self.assertEquals(
            mock_sheet.method_calls,
            [ ('save', (), {}), ]
        )


    def test_view_should_escape_naughty_characters_in_sheet_name(self):
        self.request.POST['new_value'] = '<blink>HAI!</blink>'
        response = set_sheet_name(self.request, self.user.username, self.sheet.id)
        self.assertEquals(
            response.content,
            '{"is_error":false, "html":"&lt;blink&gt;HAI!&lt;/blink&gt;"}')


SetColumnWidthsSecurityTest = create_view_security_test(
    "SetColumnWidthsSecurityTest", set_column_widths,
    post_dict={ "column_widths" : '{"2":22, "3":33}' }
)


class SetColumnWidthsTest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.get_object_or_404')
    def test_view_should_set_column_widths_and_save(self, mock_get_object):
        self.request.POST["column_widths"] = '{"2":22, "3":33}'

        sheet = Sheet()
        sheet.owner = self.user
        sheet.save = Mock()
        sheet.column_widths = {u'1':11, u'2': 22222}

        mock_get_object.return_value = sheet
        response = set_column_widths(
            self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))

        expected_col_widths = {'1':11, '2':22, '3':33}
        self.assertEquals(sheet.column_widths, expected_col_widths)

        self.assertEquals(
            sheet.save.call_args,
            ((), {})
        )


CalculateSecurityTest = create_view_security_test(
    "CalculateTest", calculate)

class CalculateTest(SheetViewTestCase):

    setUp = set_up_view_test


    @patch('sheet.views.get_object_or_404')
    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_should_use_managed_transaction_and_update_sheet_with_version_check(
        self, mock_update_sheet_with_version_check, mock_get_object_or_404
    ):

        self.sheet.unjsonify_worksheet = Mock()
        mock_update_sheet_with_version_check.return_value = True

        worksheet_after_calculate = Worksheet()

        def mock_calculate(*_):
            worksheet_after_calculate[1, 1].formula = 'calculated'
            self.sheet.jsonify_worksheet(worksheet_after_calculate)
        self.sheet.calculate = mock_calculate

        def check_transaction_managed_and_return_patched_sheet(*args, **kwargs):
            self.assertFalse(transaction.get_autocommit())
            return self.sheet
        mock_get_object_or_404.side_effect = check_transaction_managed_and_return_patched_sheet

        response = calculate(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(response.content, 'OK')

        self.assertMockUpdaterCalledOnceWithWorksheet(
            mock_update_sheet_with_version_check,
            self.sheet,
            worksheet_after_calculate
        )



    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_response_if_update_sheet_with_version_check_fails(
        self, mock_update_sheet_with_version_check
    ):
        mock_update_sheet_with_version_check.return_value = False

        actual = calculate(
            self.request, self.user.username, self.sheet.id
        )

        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(
            actual.content,
            '{ "message": "Recalc aborted: sheet changed" }'
        )


    @patch('sheet.views.get_object_or_404')
    @patch('sheet.views.Sheet.objects.get')
    @patch('sheet.views.transaction.commit')
    @patch('sheet.views.update_sheet_with_version_check')
    def test_view_merges_any_minor_changes_using_transaction(
        self, mock_update_sheet_with_version_check, mock_commit, mock_sheet_get, mock_get_object_or_404
    ):
        updated_sheet_from_db = Mock()

        self.sheet.calculate = Mock()
        self.sheet.merge_non_calc_attrs = Mock()
        mock_get_object_or_404.return_value = self.sheet

        calls = []
        self.sheet.calculate.side_effect = lambda *_, **__: calls.append("sheet.calculate")
        mock_commit.side_effect = lambda *_, **__: calls.append("commit")

        def mock_get_side_effect(*_, **__):
            calls.append("Sheet.get")
            return updated_sheet_from_db
        mock_sheet_get.side_effect = mock_get_side_effect

        self.sheet.merge_non_calc_attrs.side_effect = lambda *_, **__: calls.append("sheet.merge_non_calc_attrs")
        mock_update_sheet_with_version_check.side_effect = lambda *_, **__: calls.append("update_sheet_with_version_check")

        calculate(
            self.request, self.user.username, self.sheet.id
        )

        self.assertEquals(
            calls,
            [
                "sheet.calculate",
                "commit",
                "Sheet.get",
                "sheet.merge_non_calc_attrs",
                "update_sheet_with_version_check",
                "commit",
            ]
        )

        self.assertEquals(
            self.sheet.merge_non_calc_attrs.call_args_list,
            [((updated_sheet_from_db,), {})]
        )


    @patch('sheet.views.get_object_or_404')
    def test_view_rolls_back_and_reraises_if_sheet_calculate_raises_with_uncommitted_changes(
        self, mock_get_object_or_404
    ):

        # django.test.TestCase replaces the transaction management
        # functions with nops, which is generally useful but breaks this
        # test, as we're checking that the exception we raise isn't masked
        # by one in the leave_transaction_management saying that there was
        # a pending commit/rollback when the view returned.
        restore_transaction_methods()

        try:
            transaction.commit()
            mock_get_object_or_404.return_value = self.sheet
            original_sheet_version = self.sheet.version
            expected_exception = Exception("Expected exception")

            def mock_calculate(*_):
                self.sheet.version += 5
                self.sheet.save()
                raise expected_exception
            self.sheet.calculate = mock_calculate

            try:
                calculate(self.request, self.user.username, self.sheet.id)
                self.fail("No exception raised by calculate!")
            except Exception, e:
                self.assertEquals(e, expected_exception)

            reloaded_sheet = Sheet.objects.get(pk=self.sheet.id)
            self.assertEquals(reloaded_sheet.version, original_sheet_version)

        finally:
            # Because we committed the changes to the text fixture at the
            # start of the try/catch, we need to remove them as otherwise
            # the next test will break
            self.sheet.delete()
            self.user.delete()
            transaction.commit()
            disable_transaction_methods()


    @patch('sheet.views.get_object_or_404')
    def test_view_rolls_back_and_reraises_if_get_object_raises_with_uncommitted_changes(
        self, mock_get_object_or_404
    ):
        try:
            # django.test.TestCase replaces the transaction management
            # functions with nops, which is generally useful but breaks this
            # test, as we're checking that the exception we raise isn't masked
            # by one in the leave_transaction_management saying that there was
            # a pending commit/rollback when the view returned.

            restore_transaction_methods()
            transaction.commit()

            expected_exception = Exception("Expected exception")
            def set_dirty_and_raise_exception(*args, **kwargs):
                transaction.set_dirty()
                raise expected_exception
            mock_get_object_or_404.side_effect = set_dirty_and_raise_exception

            try:
                calculate(self.request, self.user.username, self.sheet.id)
                self.fail("No exception raised by calculate!")
            except Exception, e:
                self.assertEquals(e, expected_exception)

        finally:
            # Because we committed the changes to the text fixture at the
            # start of the try/catch, we need to remove them as otherwise
            # the next test will break
            self.sheet.delete()
            self.user.delete()
            transaction.commit()
            disable_transaction_methods()


GetJsonGridDataForUISecurityTest = create_view_security_test(
    "GetJsonGridDataForUISecurityTest",
    get_json_grid_data_for_ui,
    get_dict={'range': '1,2,3,4'}
)

class GetJsonGridDataForUITest(SheetViewTestCase):

    setUp = set_up_view_test


    @patch('sheet.views.sheet_to_ui_json_grid_data')
    @patch('sheet.views.get_object_or_404')
    def test_returns_json_grid_data_for_range_using_get_object_or_404_if_range_specified(
        self, mock_get_object, mock_sheet_to_ui_json_grid_data
    ):
        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        mock_sheet_to_ui_json_grid_data.return_value = "A random string that can live in a HttpResponse's content"
        self.request.GET['range'] = '1, 2, 3, 4'

        response = get_json_grid_data_for_ui(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertFalse(mock_sheet.calculate.called)
        self.assertCalledOnce(
            mock_sheet_to_ui_json_grid_data,
            mock_sheet.unjsonify_worksheet.return_value, (1, 2, 3, 4)
        )
        self.assertEquals(response.content, mock_sheet_to_ui_json_grid_data.return_value)


    def test_view_allows_other_users_to_view_public_sheets(self):
        self.sheet.is_public = True
        self.sheet.save()
        other_user = User(username='Othello')
        other_user.save()
        self.request.user = other_user
        self.request.GET['range'] = '1, 2, 3, 4'

        response = get_json_grid_data_for_ui(self.request, self.user.username, self.sheet.id)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('topmost' in response.content)


    def test_view_allows_anonymous_user_to_view_public_sheets(self):
        self.sheet.is_public = True
        self.sheet.save()
        self.request.user = AnonymousUser()
        self.request.META['SERVER_NAME'] = 'servername'
        self.request.META['SERVER_PORT'] = '80'
        self.request.GET['range'] = '1, 2, 3, 4'

        response = get_json_grid_data_for_ui(self.request, self.user.username, self.sheet.id)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('topmost' in response.content)


GetJsonMetaDataForUISecurityTest = create_view_security_test(
    "GetJsonMetaDataForUISecurityTest",
    get_json_meta_data_for_ui
)

class GetJsonMetaDataForUITest(SheetViewTestCase):

    setUp = set_up_view_test

    @patch('sheet.views.sheet_to_ui_json_meta_data')
    @patch('sheet.views.get_object_or_404')
    def test_get_json_meta_data_for_ui_should_return_unrecalculated_sheet_to_ui_json_using_get_object_or_404(
        self, mock_get_object, mock_sheet_to_ui_json_meta_data
    ):
        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        mock_sheet_to_ui_json_meta_data.return_value = "A random string that can live in a HttpResponse's content"

        response = get_json_meta_data_for_ui(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertFalse(mock_sheet.calculate.called)
        self.assertCalledOnce(
            mock_sheet_to_ui_json_meta_data,
            mock_sheet, mock_sheet.unjsonify_worksheet.return_value
        )
        self.assertEquals(response.content, mock_sheet_to_ui_json_meta_data.return_value)


    def test_view_allows_other_users_to_view_public_sheets(self):
        self.sheet.is_public = True
        self.sheet.name = 'lemonparty.org'
        self.sheet.save()
        other_user = User(username='Othello')
        other_user.save()
        self.request.user = other_user

        response = get_json_meta_data_for_ui(self.request, self.user.username, self.sheet.id)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('lemonparty.org' in response.content)


    def test_view_allows_anonymous_user_to_view_public_sheets(self):
        self.sheet.is_public = True
        self.sheet.name = 'lemonparty.org'
        self.sheet.save()
        self.request.user = AnonymousUser()
        self.request.META['SERVER_NAME'] = 'servername'
        self.request.META['SERVER_PORT'] = '80'

        response = get_json_meta_data_for_ui(self.request, self.user.username, self.sheet.id)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('lemonparty.org' in response.content)



class VersionUpdatesSecurityTest(SheetViewTestCase):
    '''
    dummy test class to appease metasecuritytest
    '''

class VersionUpdatesTest(SheetViewTestCase):

    setUp = set_up_view_test

    # This test merely checks that all of the views are in one of two lists
    # -- views that have to update the version and views that don't.  This is
    # done to make sure that when we add a new view, we think about whether or
    # not it should update the version.  If it shouldn't, we need do nothing
    # but put it into the no_version_update list.  If it should, we need to put
    # it into the version_update list and *also* write a test to make sure it
    # updates the version in the right way under the right circumstances; this
    # test can go in the view's own test class.
    #
    # NB we also have to explicitly ignore imports and non-functions, which
    # is a pain, but it's actually suprisingly hard to recognise an object
    # as a function, especially because it could be decorated with an object
    # that implements __call__.
    def test_all_views_considered_for_version_updates(self):

        version_update_view = [
            'calculate',
            'clear_cells',
            'clipboard',
            'import_csv',
            'set_cell_formula',
            'set_sheet_security_settings',
            'set_sheet_usercode',
        ]

        no_version_update_view = [
            'copy_sheet',
            'export_csv',
            'get_json_grid_data_for_ui',
            'get_json_meta_data_for_ui',
            'new_sheet',
            'page',
            'set_column_widths',
            'set_sheet_name',
            'import_xls',
        ]

        utility_functions = [
            'copy_sheet_to_user',
            'fetch_users_sheet',
            'fetch_users_or_public_sheet',
            'rollback_on_exception',
            'update_sheet_with_version_check',
        ]

        extra_imported_stuff_to_ignore = [
            'AnonymousUser',
            'Clipboard',
            'codecs',
            'Context',
            'datetime',
            'DirigibleImportError',
            'escape',
            'get_template',
            'HttpResponse',
            'HttpResponseForbidden',
            'HttpResponseRedirect',
            'ImportCSVForm',
            'get_object_or_404',
            'json',
            'login_required',
            'mkstemp',
            'never_cache',
            'os',
            'Q',
            'render',
            'render_to_string',
            'RequestContext',
            'reverse',
            'Sheet',
            'send_mail',
            'sheet_to_ui_json',
            'sheet_to_ui_json_grid_data',
            'sheet_to_ui_json_meta_data',
            'splitext',
            'transaction',
            'worksheet_from_excel',
            'worksheet_from_csv',
            'worksheet_to_csv',
            'wraps',
            'xlrd',
        ]

        import sheet.views
        for view_name in dir(sheet.views):
            if not re.match("__.*__", view_name):
                if (view_name not in version_update_view and
                    view_name not in no_version_update_view and
                    view_name not in utility_functions and
                    view_name not in extra_imported_stuff_to_ignore
                   ):
                    self.fail("%s not considered for version update" % (view_name,))


    def test_update_sheet_with_version_check_should_update_increment_version_and_return_true_if_no_change(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = 'old'
        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.version = 1
        self.sheet.save()

        worksheet[1, 1].formula = 'updated'
        self.sheet.jsonify_worksheet(worksheet)
        response = update_sheet_with_version_check(self.sheet, contents_json=self.sheet.contents_json)

        self.assertEquals(response, True)
        sheet_in_db = Sheet.objects.get(pk=self.sheet.id)
        self.assertEquals(sheet_in_db.version, 2)
        self.assertEquals(sheet_in_db.unjsonify_worksheet()[1, 1].formula, 'updated')


    def test_update_sheet_with_version_check_can_also_update_usercode(self):
        self.sheet.usercode = 'old'
        self.sheet.version = 1
        self.sheet.save()

        response = update_sheet_with_version_check(self.sheet, usercode='updated')

        self.assertEquals(response, True)
        sheet_in_db = Sheet.objects.get(pk=self.sheet.id)
        self.assertEquals(sheet_in_db.version, 2)
        self.assertEquals(sheet_in_db.usercode, 'updated')


    def test_update_sheet_with_version_check_returns_false_and_doesnt_update_if_sheet_changed_in_database(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = 'old'
        old_sheet = self.sheet
        old_sheet.jsonify_worksheet(worksheet)
        old_sheet.version = 1
        old_sheet.save()

        sheet_updated_elsewhere = Sheet.objects.get(pk=self.sheet.id)
        update_to_ws = Worksheet()
        update_to_ws[1, 1].formula = 'smooth and silent, just like always'
        sheet_updated_elsewhere.jsonify_worksheet(update_to_ws)
        sheet_updated_elsewhere.version += 1
        sheet_updated_elsewhere.save()

        worksheet[1, 1].formula = 'update attempt'
        old_sheet.jsonify_worksheet(worksheet)
        response = update_sheet_with_version_check(old_sheet, contents_json=old_sheet.contents_json)

        self.assertEquals(response, False)
        sheet_in_db = Sheet.objects.get(pk=self.sheet.id)
        self.assertEquals(sheet_in_db.version, 2)
        self.assertEquals(sheet_in_db.unjsonify_worksheet()[1, 1].formula, 'smooth and silent, just like always')



ClipboardViewSecurityTest = create_view_security_test(
    "ClipboardViewSecurityTest",
    clipboard,
    post_dict={'range': '2,1,3,3'},
    extra_view_args=['copy']
)


class ClipboardViewTest(SheetViewTestCase):

    setUp = set_up_view_test

    def test_copy_gets_formulas_or_formatted_values_and_populates_clipboard(self):
        self.maxDiff = None

        worksheet = Worksheet()
        b1_cell = Cell()
        b1_cell.formula= '="a formula"'
        worksheet.B1 = b1_cell

        b2_cell = Cell()
        b2_cell.formatted_value = 'formatted value only'
        worksheet.B2 = b2_cell

        b3_cell = Cell()
        b3_cell.formula = 'a constant'
        b3_cell.value = 'a value as well'
        b3_cell.formatted_value = 'another formatted value'
        worksheet.B3 = b3_cell

        self.sheet.jsonify_worksheet(worksheet)
        self.sheet.save()

        self.request.POST = {'range': '2,1,3,3'}
        response = clipboard(self.request, self.user.username, self.sheet.id, 'copy')
        self.assertEquals(response.content, 'OK')

        users_clipboard = Clipboard.objects.get(owner=self.user)

        # Setup test cells to match expectations
        b2_cell.formula = b2_cell.formatted_value
        b3_cell.value = undefined
        b3_cell.formatted_value = 'another formatted value'

        self.assertEquals(
            dict(users_clipboard.to_cells((0, 0), (1, 2))),
            {
                (0, 0):b1_cell,
                (0, 1):b2_cell,
                (0, 2):b3_cell,
                (1, 0):Cell(),
                (1, 1):Cell(),
                (1, 2):Cell(),
            }
        )


    @patch('sheet.views.update_sheet_with_version_check')
    def test_paste_offsets_range_and_updates_sheet_with_version_check(
            self, mock_update_sheet_with_version_check):
        def update_sheet_with_check(sheet, **kwargs):
            sheet.save()
            return True
        mock_update_sheet_with_version_check.side_effect = update_sheet_with_check
        self.request.POST = {'range': '3,6,3,6'}

        cb = Clipboard()
        cb.source_left = 1
        cb.source_top = 1
        cb.source_right = 1
        cb.source_bottom = 2
        cb.owner = self.user
        cb.contents_json = '{'\
                '"0,0":{"formula":"was b1", "formatted_value":"fvb1"},' \
                '"0,1":{"formula":"was b2", "formatted_value":"fvb2"}'  \
            '}'
        cb.save()

        response = clipboard(self.request, self.user.username, self.sheet.id, 'paste')
        self.assertEquals(response.content, 'OK')

        expected_worksheet = Worksheet()
        expected_worksheet[3, 6].formula = 'was b1'
        expected_worksheet[3, 6].formatted_value = 'fvb1'
        expected_worksheet[3, 7].formula = 'was b2'
        expected_worksheet[3, 7].formatted_value = 'fvb2'
        self.assertMockUpdaterCalledOnceWithWorksheet(
            mock_update_sheet_with_version_check,
            self.sheet,
            expected_worksheet
        )


    @patch('sheet.views.Clipboard')
    @patch('sheet.views.update_sheet_with_version_check')
    def test_failing_paste_returns_failure_message_and_doesnt_save_clipboard(
            self, mock_update_sheet_with_version_check, mockClipboard):
        mock_clipboard = Mock()
        mockClipboard.objects.get_or_create.return_value = mock_clipboard, False
        mock_clipboard.save = lambda: self.fail('should not save clipboard')

        mock_update_sheet_with_version_check.side_effect = lambda *a, **kw: False

        self.request.POST = {'range': '3,6,3,6'}
        response = clipboard(self.request, self.user.username, self.sheet.id, 'paste')

        self.assertEquals(
                response.content,
                '{ "message": "Paste aborted: sheet changed" }'
        )


    @patch('sheet.views.update_sheet_with_version_check')
    @patch('sheet.views.get_object_or_404')
    def test_cut_populates_and_saves_clipboard_then_removes_cells_and_saves_sheet(
        self, mock_get_object_or_404, mock_update_sheet_with_version_check
    ):
        self.maxDiff = None

        worksheet = Worksheet()
        b1_cell = Cell()
        b1_cell.formula= '="a formula"'
        worksheet.B1 = b1_cell

        b2_cell = Cell()
        b2_cell.formatted_value = 'formatted value only'
        worksheet.B2 = b2_cell

        b3_cell = Cell()
        b3_cell.formula = 'a constant'
        b3_cell.value = 'a value as well'
        b3_cell.formatted_value = 'another formatted value'
        worksheet.B3 = b3_cell

        self.sheet.jsonify_worksheet(worksheet)
        mock_get_object_or_404.return_value = self.sheet

        self.request.POST = {'range': '2,1,3,4'}
        response = clipboard(self.request, self.user.username, self.sheet.id, 'cut')
        self.assertEquals(response.content, 'OK')

        users_clipboard = Clipboard.objects.get(owner=self.user)

        # Setup test cells to match expectations
        b2_cell.formula = b2_cell.formatted_value
        b3_cell.value = undefined
        b3_cell.formatted_value = 'another formatted value'

        self.assertEquals(
            dict(users_clipboard.to_cells((0, 0), (1, 3))),
            {
                (0, 0):b1_cell,
                (0, 1):b2_cell,
                (0, 2):b3_cell,
                (0, 3):Cell(),
                (1, 0):Cell(),
                (1, 1):Cell(),
                (1, 2):Cell(),
                (1, 3):Cell(),
            }
        )

        resulting_worksheet = self.sheet.unjsonify_worksheet()
        self.assertEquals(resulting_worksheet.B1, Cell())
        self.assertEquals(resulting_worksheet.B2, Cell())
        self.assertEquals(resulting_worksheet.B3, Cell())

        self.assertEquals(users_clipboard.is_cut, True)
        self.assertEquals(users_clipboard.source_left, 2)
        self.assertEquals(users_clipboard.source_top, 1)
        self.assertEquals(users_clipboard.source_right, 3)
        self.assertEquals(users_clipboard.source_bottom, 4)
        self.assertEquals(users_clipboard.source_sheet, self.sheet)

        self.assertCalledOnce(
            mock_update_sheet_with_version_check,
            self.sheet, contents_json=self.sheet.contents_json
        )


    @patch('sheet.views.Clipboard')
    @patch('sheet.views.update_sheet_with_version_check')
    def test_failing_cut_returns_failure_message_and_doesnt_save_clipboard(
            self, mock_update_sheet_with_version_check, mockClipboard):
        mock_clipboard = Mock()
        mockClipboard.objects.get_or_create.return_value = mock_clipboard, False
        mock_clipboard.save = lambda: self.fail('should not save clipboard')

        mock_update_sheet_with_version_check.side_effect = lambda *a, **kw: False

        self.request.POST = {'range': '1,2,3,6'}
        response = clipboard(self.request, self.user.username, self.sheet.id, 'cut')

        self.assertEquals(
                response.content,
                '{ "message": "Cut aborted: sheet changed" }'
        )


    @patch('sheet.views.Clipboard')
    def test_copy_then_paste_both_save_clipboard_appropriately(self, mockClipboard):
        mock_clipboard = Mock()
        mockClipboard.objects.get_or_create.return_value = mock_clipboard, False

        self.request.POST = {'range': '2,1,3,4'}
        clipboard(self.request, self.user.username, self.sheet.id, 'copy')
        self.assertCalledOnce(mock_clipboard.copy, self.sheet, (2, 1), (3, 4))
        self.assertCalledOnce(mock_clipboard.save)

        mock_clipboard.reset_mock()
        self.request.POST = {'range': '4,5,4,5'}
        clipboard(self.request, self.user.username, self.sheet.id, 'paste')
        self.assertCalledOnce(mock_clipboard.paste_to, self.sheet, (4, 5), (4, 5))
        self.assertCalledOnce(mock_clipboard.save)


    @patch('sheet.views.Clipboard')
    def test_cut_then_paste_to_same_sheet(self, mockClipboard):
        mock_clipboard = Mock()
        mockClipboard.objects.get_or_create.return_value = mock_clipboard, False

        self.request.POST = {'range': '2,1,3,4'}
        clipboard(self.request, self.user.username, self.sheet.id, 'cut')
        self.assertCalledOnce(mock_clipboard.cut, self.sheet, (2, 1), (3, 4))
        self.assertCalledOnce(mock_clipboard.save)

        mock_clipboard.reset_mock()

        self.request.POST = {'range': '4,5,4,5'}
        clipboard(self.request, self.user.username, self.sheet.id, 'paste')
        self.assertCalledOnce(mock_clipboard.paste_to, self.sheet, (4, 5), (4, 5))
        self.assertCalledOnce(mock_clipboard.save)



class MetaSecurityTest(SheetViewTestCase):
    def test_security_classes_exist(self):
        assert_security_classes_exist(self, __name__, excludes=['SheetViewTestCase'])

