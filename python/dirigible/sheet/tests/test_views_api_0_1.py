# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import simplejson as json
except ImportError:
    import json

try:
    import unittest2 as unittest
except ImportError:
    import sys
    assert sys.version.startswith('2.7')
    import unittest


from datetime import datetime, timedelta
from mock import Mock, patch

import django
from django.contrib.auth.models import User
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.test.testcases import disable_transaction_methods, restore_transaction_methods

from sheet.models import Sheet
from sheet.worksheet import Worksheet
from sheet.tests.test_views import set_up_view_test
from test_utils import ResolverTestMixins
from user.models import OneTimePad

from sheet.views_api_0_1 import calculate_and_get_json_for_api, _sheet_to_value_only_json


pk_name = 'dirigible_l337_private_key'



class CalculateAndGetJsonForApiViewTest(django.test.TestCase, ResolverTestMixins):

    setUp = set_up_view_test

    def tearDown(self):
        User.objects.all().delete()


    def test_api_view_should_return_404_if_sheet_owner_does_not_match_username_from_url(self):
        #standard security test
        self.sheet.allow_json_api_access = False
        self.sheet.save()
        self.request.user = User()
        self.assertRaises(Http404, lambda: calculate_and_get_json_for_api(self.request, 'some_random_user', self.sheet.id))


    def test_api_view_returns_403_if_neither_private_nor_api_keys_provided(self):
        actual = calculate_and_get_json_for_api(self.request, self.sheet.owner.username, self.sheet.id)
        self.assertTrue(isinstance(actual, HttpResponseForbidden))


    def test_api_view_returns_403_if_incorrect_private_key_provided(self):
        self.request.method = 'POST'
        self.request.POST = {pk_name: 'an incorrect key'}
        actual = calculate_and_get_json_for_api(self.request, self.sheet.owner.username, self.sheet.id)
        self.assertTrue(isinstance(actual, HttpResponseForbidden))


    def test_api_view_works_if_correct_private_key_provided(self):
        self.request.method = 'POST'
        self.request.POST = {pk_name: self.sheet.create_private_key()}
        actual = calculate_and_get_json_for_api(self.request, self.sheet.owner.username, self.sheet.id)
        self.assertTrue(json.loads(actual.content), {'name': self.sheet.name})


    @patch('sheet.views_api_0_1.OneTimePad')
    def test_api_view_erm_checks_private_key_using_correct_filter(
        self, mock_Otp):

        mock_Otp.objects.filter.return_value = []
        guid = self.sheet.create_private_key()
        self.request.method = 'POST'
        self.request.POST = {pk_name: guid}

        actual = calculate_and_get_json_for_api(
            self.request,
            self.sheet.owner.username,
            self.sheet.id)

        self.assertCalledOnce(
            mock_Otp.objects.filter,
            user=self.sheet.owner, guid=guid)


    def test_api_view_ignores_old_private_key_things(self):
        otp = OneTimePad(user=self.user)
        otp.save()
        otp.creation_time = datetime.today() - timedelta(36000)
        otp.save()
        guid = otp.guid
        self.request.method = 'POST'
        self.request.POST = {pk_name: guid}

        actual = calculate_and_get_json_for_api(
            self.request,
            self.sheet.owner.username,
            self.sheet.id)

        self.assertTrue(isinstance(actual, HttpResponseForbidden))



    def test_api_view_403s_if_no_private_key_and_api_access_not_allowed_even_if_correct_api_key_provided(self):
        self.sheet.allow_json_api_access = False
        self.sheet.api_key = 'correct key'
        self.sheet.save()
        self.request.method = 'POST'
        self.request.POST = {'api_key': 'correct key'}
        actual = calculate_and_get_json_for_api(self.request, self.sheet.owner.username, self.sheet.id)
        self.assertTrue(isinstance(actual, HttpResponseForbidden))


    def test_api_view_403s_if_api_access_allowed_but_incorrect_api_key_provided(self):
        self.sheet.allow_json_api_access = True
        self.sheet.save()
        self.request.method = 'POST'
        self.request.POST = {'api_key': 'an incorrect key'}
        actual = calculate_and_get_json_for_api(self.request, self.sheet.owner.username, self.sheet.id)
        self.assertTrue(isinstance(actual, HttpResponseForbidden))


    def test_api_view_works_if_correct_api_key_provided_and_access_allowed(self):
        self.sheet.allow_json_api_access = True
        self.sheet.api_key = 'sekrit'
        self.sheet.save()
        self.request.method = 'POST'
        self.request.POST = {'api_key': 'sekrit'}
        actual = calculate_and_get_json_for_api(self.request, self.sheet.owner.username, self.sheet.id)
        self.assertTrue(json.loads(actual.content), {'name': self.sheet.name})


    @patch('sheet.views_api_0_1.transaction')
    @patch('sheet.views_api_0_1.get_object_or_404')
    def test_api_view_should_call_sheet_calculate_with_transaction(
        self, mock_get_object, mock_transaction
    ):
        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        mock_sheet.allow_json_api_access = True
        transaction = Mock()
        def wrapper(view):
            def inner(*_, **__):
                view(*_, **__)
            return inner
        mock_transaction.commit_manually = wrapper

        self.request.method = 'POST'
        self.request.POST['api_key'] = mock_sheet.api_key = 'key'

        mock_sheet.unjsonify_worksheet.return_value = Worksheet()

        response = calculate_and_get_json_for_api(self.request, self.user.username, self.sheet.id)

        self.assertEquals(
            mock_sheet.calculate.call_args_list,
            [((), {})]
        )
        self.assertCalledOnce(mock_transaction.commit)


    @patch('sheet.views_api_0_1.get_object_or_404')
    def test_api_view_rolls_back_and_reraises_if_get_object_raises_with_uncommitted_changes(
        self, mock_get_object_or_404
    ):
        try:
            # django.test.TestCase replaces the transaction management functions with nops,
            # which is generally useful but breaks this test, as we're checking that the
            # exception we raise isn't masked by one in the leave_transaction_management
            # saying that there was a pending commit/rollback when the view returned.
            restore_transaction_methods()
            transaction.commit()

            expected_exception = Exception("Expected exception")
            def set_dirty_and_raise_exception(*args, **kwargs):
                transaction.set_dirty()
                raise expected_exception
            mock_get_object_or_404.side_effect = set_dirty_and_raise_exception

            try:
                calculate_and_get_json_for_api(self.request, self.user.username, self.sheet.id)
            except Exception, e:
                self.assertEquals(e, expected_exception)
            else:
                self.fail("No exception raised by calculate_and_get_json_for_api!")

        finally:
            # Because we committed the changes to the text fixture at the
            # start of the try/catch, we need to remove them as otherwise
            # the next test will break
            self.sheet.delete()
            self.user.delete()
            transaction.commit()
            disable_transaction_methods()


    @patch('sheet.views_api_0_1.get_object_or_404')
    def test_api_view_adds_access_control_header(
        self, mock_get_object
    ):
        calculation_result = Worksheet()
        calculation_result[1, 3].formula = '=string'
        calculation_result[1, 3].value = 'test value'
        calculation_result[2, 5].formula = '=int'
        calculation_result[2, 5].value = 6

        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user
        mock_sheet.unjsonify_worksheet.side_effect = lambda: calculation_result
        mock_sheet.name = 'mock sheet'
        mock_sheet.allow_json_api_access = True
        self.request.method = 'POST'
        self.request.POST['api_key'] = mock_sheet.api_key = 'key'

        actual = calculate_and_get_json_for_api(self.request, self.user.username, self.sheet.id)

        self.assertEquals(actual['Access-Control-Allow-Origin'], '*')


    @patch('sheet.views_api_0_1.transaction')
    @patch('sheet.views_api_0_1.get_object_or_404')
    def test_api_view_commits_transaction_even_on_sheet_calculate_exception(
        self, mock_get_object, mock_transaction
    ):
        mock_sheet = mock_get_object.return_value
        mock_sheet.calculate = self.die
        mock_sheet.owner = self.user
        mock_sheet.allow_json_api_access = True
        self.request.method = 'POST'
        self.request.POST['api_key'] = mock_sheet.api_key = 'key'

        actual = calculate_and_get_json_for_api(
            self.request, self.user.username, self.sheet.id)

        self.assertCalledOnce(mock_transaction.commit)
        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content, 'should not be called')


    @patch('sheet.views_api_0_1.get_object_or_404')
    def test_api_view_should_return_errors_and_no_values_if_unjsonify_worksheet_result_has_errors(self, mock_get_object):
        mock_sheet = mock_get_object.return_value
        mock_sheet.owner = self.user

        worksheet = Worksheet()
        worksheet[1, 3].formula = '=string'
        worksheet[1, 3].value = 'test value'
        worksheet._usercode_error = {
            "message": "I am an error message",
            "line": 2
        }
        mock_sheet.unjsonify_worksheet.side_effect = lambda: worksheet
        mock_sheet.allow_json_api_access = True
        self.request.method = 'POST'
        self.request.POST['api_key'] = mock_sheet.api_key = 'key'

        expected_json = {
            "usercode_error" : {
                "message": "I am an error message",
                "line": "2"
            }
        }

        actual = calculate_and_get_json_for_api(self.request, self.user.username, self.sheet.id)

        self.assertFalse(mock_sheet.save.called)
        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content, json.dumps(expected_json))


    def die(*_):
        raise AssertionError('should not be called')


    @patch('sheet.views_api_0_1.get_object_or_404')
    def test_api_view_should_handle_cell_formula_overrides_from_POST(self, mock_get_object):
        mock_sheet = mock_get_object.return_value = Sheet()
        mock_sheet.owner = self.user

        worksheet = Worksheet()
        worksheet[1, 1].formula = 'initial-formula1'
        worksheet[2, 1].formula = '222'
        worksheet[3, 1].formula = '=B1+111'
        mock_sheet.jsonify_worksheet(worksheet)
        mock_sheet.name = 'mysheet'
        mock_sheet.allow_json_api_access = True

        mock_sheet.save = self.die

        self.request.method = 'POST'
        self.request.POST = {
            u'1,1':u'overriddenformula',
            u'D1':u'=B1+222',
        }
        self.request.POST['api_key'] = mock_sheet.api_key = 'key'

        response = calculate_and_get_json_for_api(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        expected_json = {
            'name': 'mysheet',
            '1' : {
                '1': 'overriddenformula',
            },
            '2': {
                '1': 222,
            },
            '3': {
                '1': 333,
            },
            '4': {
                '1': 444,
            },
        }
        self.assertEquals(json.loads(response.content), expected_json)



    @patch('sheet.views_api_0_1.get_object_or_404')
    def test_api_view_should_handle_cell_formula_overrides_from_GET(self, mock_get_object):
        mock_sheet = mock_get_object.return_value = Sheet()
        mock_sheet.owner = self.user

        worksheet = Worksheet()
        worksheet[1, 1].formula = 'initial-formula1'
        worksheet[2, 1].formula = '222'
        worksheet[3, 1].formula = '=B1+111'
        mock_sheet.jsonify_worksheet(worksheet)
        mock_sheet.name = 'mysheet'
        mock_sheet.allow_json_api_access = True
        mock_sheet.api_key = 'key'

        mock_sheet.save = self.die

        self.request.GET = {
            u'1,1':u'overriddenformula',
            u'D1':u'=B1+222',
            'api_key': 'key'
        }
        self.request.method = 'GET'

        response = calculate_and_get_json_for_api(self.request, self.user.username, self.sheet.id)

        self.assertTrue(isinstance(response, HttpResponse))
        expected_json = {
            'name': 'mysheet',
            '1' : {
                '1': 'overriddenformula',
            },
            '2': {
                '1': 222,
            },
            '3': {
                '1': 333,
            },
            '4': {
                '1': 444,
            },
        }
        self.assertEquals(json.loads(response.content), expected_json)



class TestSheetToValueOnlyJson(unittest.TestCase):

    def test_sheet_to_value_only_json_for_empty_worksheet(self):
        expected = dict(name='A sheet name')
        result = _sheet_to_value_only_json("A sheet name", Worksheet())
        self.assertEquals(json.loads(result), expected)


    def test_sheet_to_value_only_json_with_content(self):
        worksheet = Worksheet()
        worksheet[2, 1].formula = 'Row 1, col 2 formula'
        worksheet[2, 1].value = 'Row 1, col 2 value'
        worksheet[10, 1].formula = 'Row 1, col 10 formula'
        worksheet[10, 1].value = 'Row 1, col 10 value'
        worksheet[1, 5].formula = 'Row 5, col 1 formula'
        worksheet[1, 5].value = 'Row 5, col 1 value'
        worksheet[10, 5].formula = u'Row 5, col 10 formula avec un \xe9'
        worksheet[10, 5].value = u'Row 5, col 10 value avec un autre \xe9'

        expected_json_contents = {
            'name': "Sheet name",
            '1': {
                '5': "Row 5, col 1 value",
            },
            '2': {
                '1': "Row 1, col 2 value",
            },
            '10': {
                '1': "Row 1, col 10 value",
                '5': u"Row 5, col 10 value avec un autre \xe9",
            }
        }
        result = _sheet_to_value_only_json("Sheet name", worksheet)
        self.assertEquals(json.loads(result), expected_json_contents)


    def test_sheet_to_value_only_json_does_not_include_errors(self):
        self.maxDiff = None

        worksheet = Worksheet()
        worksheet.A1.formula = 'a broken formula'
        worksheet.A1.error = 'TestingError'
        worksheet.A2.formula = 'an OK formula'
        worksheet.A2.value = "23"
        expected_json_contents = {
            'name': "Sheet name",
            '1' : {
                '2' : '23',
            }
        }
        result = _sheet_to_value_only_json("Sheet name", worksheet)
        self.assertEquals(json.loads(result), expected_json_contents)


    def test_sheet_to_value_only_json_non_string_cell_values(self):
        known_object = object()
        worksheet = Worksheet()
        worksheet.A1.formula = 'an int'
        worksheet.A1.value = 123
        worksheet.A2.formula = 'a float'
        worksheet.A2.value = 1.25
        worksheet.A3.formula = 'a list'
        worksheet.A3.value = [1, 2, 3]
        worksheet.A4.formula = 'an object'
        worksheet.A4.value = known_object
        expected_ko = unicode(known_object)
        expected_json_contents = {
            'name': "Sheet name",
            '1' : {
                '1' : 123,
                '2' : 1.25,
                '3' : [1, 2, 3],
                '4' : expected_ko,
            },
        }
        result = _sheet_to_value_only_json("Sheet name", worksheet)
        self.assertEquals(json.loads(result), expected_json_contents)

