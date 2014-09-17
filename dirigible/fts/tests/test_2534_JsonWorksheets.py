# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import simplejson as json
except ImportError:
    import json

from urllib import urlencode
from urllib2 import urlopen

from functionaltest import FunctionalTest, Url


class Test_2534_JsonWorksheets_v0_1(FunctionalTest):

    def enable_json_api_for_sheet(self):
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.selenium.click('id=id_security_form_json_enabled_checkbox')
        self.selenium.type('id=id_security_form_json_api_key', self.get_my_username())
        self.selenium.click('id=id_security_form_ok_button')
        self.wait_for_element_visibility('id=id_security_form', False)


    def test_simple_json(self):
        # * Harold wants to use Dirigible to run his spreadsheets using
        #   a json-based rest API

        # * He logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # * He enables json api access for the sheet
        self.enable_json_api_for_sheet()

        # * He enters some values and formulae
        self.enter_cell_text(1, 1, '5')
        self.enter_cell_text(1, 2, 'abc')
        self.enter_cell_text(2, 1, '6')
        self.enter_cell_text(3, 1, '=a1 + b1')
        self.wait_for_cell_value(3, 1, '11')
        # * He uses an API call to get the sheet as JSON
        sheet_content = json.load(urlopen(Url.api_url(self.get_my_username(), sheet_id), data=urlencode({'api_key': self.get_my_username()})))

        expected = {
            'name' : 'Sheet %s' % (sheet_id,),
            '1': {
                '1': 5,
                '2': 'abc'
                },
            '2': {
                '1': 6,
                },
            '3': {
                '1': 11
            },
        }
        self.assertEquals(sheet_content, expected)


    def test_simple_json_with_error(self):
        # * Harold wants to use Dirigible to run his spreadsheets using
        #   a json-based rest API, and wants the error-handling to be
        #   well-defined (if perhaps not ideal from a debugging perspective)


        # * He logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # * He enables json api access for the sheet
        self.enable_json_api_for_sheet()

        # * He enters a single formula operating on a single value
        self.enter_cell_text(1, 1, '5')
        self.enter_cell_text(1, 2, '=1/A1')
        self.wait_for_cell_value(1, 2, '0.2')

        # * He uses an API call to get the sheet as JSON, passing in an override
        #   value that he knows will cause an error
        get_params = urlencode({'A1':'0', 'api_key': self.get_my_username()})
        url = '%s?%s' % (Url.api_url(self.get_my_username(), sheet_id), get_params)
        try:
            sheet_content = json.load(urlopen(url))
        except Exception, e:
            self.fail(str(e))

        # * He gets back nothing for the cell which generated an error,
        expected = {
            'name' : 'Sheet %s' % (sheet_id,),
            '1': {
                '1': 0,
            },
        }
        self.assertEquals(sheet_content, expected)


    def test_simple_json_with_overrides_get(self):
        # * Harold wants to use Dirigible to run his spreadsheets using
        #   a json-based rest API, and override the formula of some cells

        # * He logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # * He enables json api access for the sheet
        self.enable_json_api_for_sheet()

        # * He enters some values and formulae
        self.enter_cell_text(1, 1, '5')         # A1
        self.enter_cell_text(1, 2, 'abc')       # A2
        self.enter_cell_text(2, 1, '6')         # B1
        self.enter_cell_text(3, 1, '=a1 + b1')  # C1
        self.wait_for_cell_value(3, 1, '11')

        # * He uses an API call to get the sheet as JSON
        #   but overrides the values of cells using GET params:
        #       B1=11
        #       C2=A1 + 1
        #   this also causes cell C1 to change value, since it
        #   depends on B1
        get_params = urlencode({'2,1':'11', 'C2':'=A1 + 1', 'api_key': self.get_my_username()})
        url = '%s?%s' % (Url.api_url(self.get_my_username(), sheet_id), get_params)
        try:
            sheet_content = json.load(urlopen(url))
        except Exception, e:
            self.fail(str(e))

        expected = {
            'name' : 'Sheet %s' % (sheet_id,),
            '1': {
                '1': 5,
                '2': 'abc'
                },
            '2': {
                '1': 11,
                },
            '3': {
                '1': 16,
                '2': 6
            },
        }
        self.assertEquals(sheet_content, expected)


    def test_simple_json_with_overrides_post(self):
        # * Harold wants to use Dirigible to run his spreadsheets using
        #   a json-based rest API, and override the formula of some cells

        # * He logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # * He enables json api access for the sheet
        self.enable_json_api_for_sheet()

        # * He enters some values and formulae
        self.enter_cell_text(1, 1, '5')         # A1
        self.enter_cell_text(1, 2, 'abc')       # A2
        self.enter_cell_text(2, 1, '6')         # B1
        self.enter_cell_text(3, 1, '=a1 + b1')  # C1
        self.wait_for_cell_value(3, 1, '11')

        # * He uses an API call to get the sheet as JSON
        #   but overrides the values of cells using POST params:
        #       B1=11
        #       C2=A1 + 1
        #   this also causes cell C1 to change value, since it
        #   depends on B1
        url = Url.api_url(self.get_my_username(), sheet_id)
        post_params = urlencode({'2,1':'11', 'C2':'=A1 + 1', 'api_key': self.get_my_username()})
        try:
            sheet_content = json.load(urlopen(url, data=post_params))
        except Exception, e:
            self.fail(str(e))

        expected = {
            'name' : 'Sheet %s' % (sheet_id,),
            '1': {
                '1': 5,
                '2': 'abc'
                },
            '2': {
                '1': 11,
                },
            '3': {
                '1': 16,
                '2': 6
            },
        }
        self.assertEquals(sheet_content, expected)

