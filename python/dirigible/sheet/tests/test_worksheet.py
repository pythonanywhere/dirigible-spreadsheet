# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import with_statement

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import codecs
import jsonlib
import simplejson as json
from StringIO import StringIO
from mock import Mock, patch
from threading import Thread

from test_utils import ResolverTestCase

from sheet.cell import Cell, undefined

from sheet.worksheet import (
    Bounds, InvalidKeyError, Worksheet, worksheet_to_csv,
    worksheet_to_json, worksheet_from_json,
)


class WorksheetToCsvTest(ResolverTestCase):

    @patch('dirigible.sheet.worksheet.csv')
    @patch('dirigible.sheet.worksheet.StringIO')
    def test_should_use_stringio_and_return_result(self, mock_stringio_class, mock_csv):
        mock_stringio_object = mock_stringio_class.return_value

        def check_getvalue_has_been_called():
            self.assertCalledOnce(mock_stringio_object.getvalue)
        mock_stringio_object.close.side_effect = check_getvalue_has_been_called

        ws = Worksheet()
        ws.A1.value = "test data"
        result = worksheet_to_csv(ws, encoding='ascii')

        self.assertCalledOnce(mock_csv.writer, mock_stringio_object)
        self.assertEquals(result, mock_stringio_object.getvalue.return_value)
        self.assertCalledOnce(mock_stringio_object.close)


    @patch('dirigible.sheet.worksheet.csv')
    def test_should_handle_empty_worksheet(self, mock_csv):
        ws = Worksheet()

        result = worksheet_to_csv(ws, encoding='ascii')

        mock_writer = mock_csv.writer.return_value
        self.assertFalse(mock_writer.writerow.called)


    def test_should_convert_unicode_to_windows_1252(self):
        ws = Worksheet()
        ws.a1.value = u'Sacr\xe9 bleu!'
        ws.a2.value = u'\xa312.95'
        ws.a3.value = u'\u20ac9.99'
        result = worksheet_to_csv(ws, encoding='windows-1252')
        self.assertEquals(
                result.split('\r\n')[:-1],
                [
                    ws.a1.value.encode('windows-1252'),
                    ws.a2.value.encode('windows-1252'),
                    ws.a3.value.encode('windows-1252'),
                ]
        )


    def test_raises_on_attempting_to_encode_nonwestern_chars_to_excel_format(self):
        some_kanji = u'\u30bc\u30ed\u30a6\u30a3\u30f3\u30b0'
        ws = Worksheet()
        ws.a1.value = some_kanji
        self.assertRaises(
            UnicodeEncodeError,
            lambda : worksheet_to_csv(ws, encoding='windows-1252')
        )


    def test_handles_cell_values_set_to_non_ascii_bytes(self):
        a_large_number = 25700000000.0
        ws = Worksheet()
        ws.a1.value = a_large_number
        result = worksheet_to_csv(ws, encoding='windows-1252')
        stream = StringIO()
        stream.write(result)
        stream.seek(0)
        decoder = codecs.getreader('windows-1252')(stream)
        decoder.read()


    def test_can_convert_unicode_to_utf8(self):
        some_kanji = u'\u30bc\u30ed\u30a6\u30a3\u30f3\u30b0'
        ws = Worksheet()
        ws.a1.value = some_kanji
        result = worksheet_to_csv(ws, encoding='utf-8')
        self.assertEquals(
                result.split('\r\n')[:-1],
                [
                    ws.a1.value.encode('utf-8'),
                ]
        )


    @patch('dirigible.sheet.worksheet.csv')
    def test_should_process_contents_in_raster_order(self, mock_csv):
        ws = Worksheet()
        ws.A1.value = 1
        ws.B1.value = 2
        ws.C1.value = 3
        ws.A2.value = 4
        ws.B2.value = 5
        ws.C2.value = 6

        result = worksheet_to_csv(ws, encoding='windows-1252')

        mock_writer = mock_csv.writer.return_value
        self.assertEquals(
            mock_writer.writerow.call_args_list,
            [
                (([1, 2, 3],), {}),
                (([4, 5, 6],), {})
            ]
        )


    @patch('dirigible.sheet.worksheet.csv')
    def test_should_include_everything_from_A1_outwards(self, mock_csv):
        ws = Worksheet()
        ws.B3.value = 5

        result = worksheet_to_csv(ws, encoding='windows-1252')

        mock_writer = mock_csv.writer.return_value
        self.assertEquals(
            mock_writer.writerow.call_args_list,
            [
                ((["", ""],), {}),
                ((["", ""],), {}),
                ((["", 5],), {})
            ]
        )



class WorksheetJSONificationTest(ResolverTestCase):

    def test_empty_worksheet_to_json(self):
        worksheet = Worksheet()

        worksheet_json = worksheet_to_json(worksheet)
        self.assertEquals(
            json.loads(worksheet_json),
            {
                "_console_text": "",
                "_usercode_error": None,
            }
        )


    @patch('dirigible.sheet.worksheet.StringIO')
    def test_worksheet_to_json_remembers_to_close_stringIO_stream(self, mock_stringio):
        worksheet = Worksheet()
        mock_stringio.return_value = Mock()
        worksheet_to_json(worksheet)
        self.assertCalledOnce(mock_stringio.return_value.close)


    def test_worksheet_with_data_to_json(self):
        self.maxDiff = None

        worksheet = Worksheet()

        worksheet.B29.formula = "a constant"
        worksheet.B29.value = 56
        worksheet.B29.formatted_value = "fifty-six"
        worksheet.B29.error = "b0rken"

        worksheet.C29.formula = "another constant"
        worksheet.C29.value = ["value", "is", "a", "list"]
        worksheet.C29.formatted_value = "[the same list]"

        class UnJSONableObject(object):
            def __str__(self):
                return "The result of str-ing the object"
        worksheet.D29.formula = None
        worksheet.D29.value = UnJSONableObject()
        worksheet.D29.formatted_value = "The formatted object"

        worksheet.E29.formula = '=1 + 2'
        worksheet.E29.value = 3
        worksheet.E29.formatted_value = "Three"

        worksheet._console_text = "The console text"
        worksheet._usercode_error = { "message": "The usercode error", "line": 23 }

        worksheet_json = worksheet_to_json(worksheet)

        self.assertEquals(
            json.loads(worksheet_json),
            {
                u"2,29" : {
                    u"formula" : u"a constant",
                    u"value" : 56,
                    u"formatted_value": u"fifty-six",
                    u"error": u"b0rken"
                },

                u"3,29" : {
                    u"formula" : u"another constant",
                    u"value" : [u"value", u"is", u"a", u"list"],
                    u"formatted_value": u"[the same list]"
                },

                u"4,29" : {
                    u"formula" : None,
                    u"formatted_value": u"The formatted object",
                },

                u"5,29" : {
                    u"formula" : u"=1 + 2",
                    u"python_formula" : u"1 + 2",
                    u"value": 3,
                    u"formatted_value": u"Three",
                },

                u"_console_text": u"The console text",
                u"_usercode_error": { u"message": u"The usercode error", u"line": 23 },
            }
        )


    def test_dependencies_get_put_in_json_as_array_of_arrays(self):
        self.maxDiff = None

        worksheet = Worksheet()
        worksheet.A1.dependencies = [(1, 2)]
        worksheet._console_text = ""

        worksheet_json = worksheet_to_json(worksheet)

        self.assertEquals(
            json.loads(worksheet_json),
            {
                u"1,1" : {
                    u"formula" : None,
                    u"formatted_value" : u"",
                    u"dependencies" : [[1, 2]],
                },

                u"_console_text": u"",
                u"_usercode_error": None,
            }
        )


    def test_nan_values_are_ignored(self):
        self.maxDiff = None

        worksheet = Worksheet()
        worksheet.A1.value = float('nan')
        worksheet.A2.value = float('inf')
        worksheet.A3.value = float('-inf')

        worksheet_json = worksheet_to_json(worksheet)
        roundtripped = jsonlib.read(worksheet_json)
        self.assertEquals(roundtripped["1,1"]['formatted_value'], 'nan')
        self.assertEquals(roundtripped["1,2"]['formatted_value'], 'inf')
        self.assertEquals(roundtripped["1,3"]['formatted_value'], '-inf')
        self.assertFalse('value' in roundtripped["1,1"])
        self.assertFalse('value' in roundtripped["1,2"])
        self.assertFalse('value' in roundtripped["1,3"])


    def test_empty_worksheet_from_json(self):
        worksheet = worksheet_from_json(
            json.dumps(
                {
                    "_console_text": "",
                    "_usercode_error": None,
                }
            )
        )

        self.assertEquals(worksheet._console_text, "")
        self.assertEquals(worksheet._usercode_error, None)
        self.assertIsNotNone(worksheet._console_lock)


    def test_worksheet_with_data_from_json(self):
        worksheet = worksheet_from_json(
            json.dumps(
                {
                    "2,29" : {
                        "formula" : "a formula",
                        "value" : 56,
                        "dependencies" : [[4, 3], [2, 1]],
                        "formatted_value": "fifty-six",
                        "error": "b0rken"
                    },

                    "3,29" : {
                        "formula" : "another formula",
                        "value" : ["value", "is", "a", "list"],
                        "formatted_value": "[the same list]"
                    },

                    "4,29" : {
                        "formula" : None,
                        "formatted_value": "The formatted object",
                    },

                    "5,29" : {
                        "formula" : "=2 + 4",
                        "python_formula" : "2 + 4",
                        "value" : 6,
                        "formatted_value": "six",
                    },

                    "6,29" : {
                        "formula" : "=I don't have a python formula. I don't want one.",
                        "value" : 7,
                        "formatted_value": "seven",
                    },

                    "_console_text": "The console text",
                    "_usercode_error": { "message": "The usercode error", "line": 23 },
                }
            )
        )

        self.assertEquals(worksheet.B29.formula, "a formula")
        self.assertEquals(worksheet.B29.python_formula, None)
        self.assertEquals(worksheet.B29.dependencies, [(4, 3), (2, 1)])
        self.assertEquals(worksheet.B29.value, 56)
        self.assertEquals(worksheet.B29.formatted_value, "fifty-six")
        self.assertEquals(worksheet.B29.error, "b0rken")

        self.assertEquals(worksheet.C29.formula, "another formula")
        self.assertEquals(worksheet.C29.python_formula, None)
        self.assertEquals(worksheet.C29.value, ["value", "is", "a", "list"])
        self.assertEquals(worksheet.C29.formatted_value, "[the same list]")

        self.assertEquals(worksheet.D29.formula, None)
        self.assertEquals(worksheet.D29.python_formula, None)
        self.assertEquals(worksheet.D29.value, undefined)
        self.assertEquals(worksheet.D29.formatted_value, "The formatted object")

        self.assertEquals(worksheet.E29.formula, "=2 + 4")
        self.assertEquals(worksheet.E29.python_formula, "2 + 4")
        self.assertEquals(worksheet.E29.value, 6)
        self.assertEquals(worksheet.E29.formatted_value, "six")

        self.assertEquals(worksheet.F29.formula, "=I don't have a python formula. I don't want one.")
        self.assertEquals(worksheet.F29.python_formula, None)
        self.assertEquals(worksheet.F29.value, 7)
        self.assertEquals(worksheet.F29.formatted_value, "seven")

        self.assertEquals(worksheet._console_text, "The console text")
        self.assertEquals(worksheet._usercode_error, { "message": "The usercode error", "line": 23 })
        self.assertIsNotNone(worksheet._console_lock)


    @patch('dirigible.sheet.worksheet.jsonlib')
    def test_worksheet_from_json_uses_jsonlib(self, mock_jsonlib):
        mock_jsonlib.read.return_value = {}
        worksheet_from_json('{}')
        self.assertCalledOnce(mock_jsonlib.read, '{}')



class WorksheetTest(unittest.TestCase):

    def test_initialise(self):
        ws = Worksheet()
        self.assertEquals(dict(ws), {})
        self.assertEquals(ws._console_text, '')
        self.assertEquals(ws._usercode_error, None)
        self.assertEquals(ws.name, None)


    def test_repr(self):
        ws = Worksheet()
        self.assertEquals(repr(ws), '<Worksheet>')

        ws.name = 'test worksheet'
        self.assertEquals(repr(ws), '<Worksheet test worksheet>')

    def test_equality(self):
        ws1 = Worksheet()
        ws2 = Worksheet()
        ws2.A1.formula = 'a difference'
        self.assertFalse(ws1==ws2)
        self.assertTrue(ws1!=ws2)

        ws3 = Worksheet()
        self.assertTrue(ws1==ws3)
        self.assertFalse(ws1!=ws3)

        ws3.name = 'a different name!'
        self.assertFalse(ws1==ws3)
        self.assertTrue(ws1!=ws3)

        nonWs = 1.2
        self.assertFalse(ws1==nonWs)
        self.assertTrue(ws1!=nonWs)


    def test_append_console_text(self):
        ws = Worksheet()
        ws.add_console_text('a first error')
        self.assertEquals(
            ws._console_text,
            '<span class="console_error_text">a first error</span>')

        ws.add_console_text('a second error\noh noez!')
        self.assertEquals(
            ws._console_text,
            '<span class="console_error_text">a first error</span>'
            '<span class="console_error_text">a second error\n'
            'oh noez!</span>')

        ws.add_console_text('not an error', log_type='output')
        self.assertEquals(
            ws._console_text,
            '<span class="console_error_text">a first error</span>'
            '<span class="console_error_text">a second error\n'
            'oh noez!</span>'
            '<span class="console_output_text">not an error</span>')

        ws.add_console_text('A system timing report, for example :-)', log_type='system')
        self.assertEquals(
            ws._console_text,
            '<span class="console_error_text">a first error</span>'
            '<span class="console_error_text">a second error\n'
            'oh noez!</span>'
            '<span class="console_output_text">not an error</span>'
            '<span class="console_system_text">A system timing report, for example :-)</span>')

        ws.add_console_text('<b></b>', log_type='output')
        self.assertEquals(
            ws._console_text,
            '<span class="console_error_text">a first error</span>'
            '<span class="console_error_text">a second error\n'
            'oh noez!</span>'
            '<span class="console_output_text">not an error</span>'
            '<span class="console_system_text">A system timing report, for example :-)</span>'
            '<span class="console_output_text">&lt;b&gt;&lt;/b&gt;</span>')


    def test_to_location(self):
        ws = Worksheet()

        self.assertEquals( ws.to_location((1, 2)), (1, 2) )
        self.assertEquals( ws.to_location((1L, 2L)), (1L, 2L) )
        self.assertEquals( ws.to_location(('a', 2)), (1, 2) )
        self.assertEquals( ws.to_location(('A', 2)), (1, 2) )
        self.assertEquals( ws.to_location('a2'), (1, 2) )
        self.assertEquals( ws.to_location('A2'), (1, 2) )

        self.assertEquals( ws.to_location('A'), None )
        self.assertEquals( ws.to_location('1A'), None )
        self.assertEquals( ws.to_location((1, 'A')), None )
        self.assertEquals( ws.to_location(123), None )
        self.assertEquals( ws.to_location(object()), None )


    def test_setitem_on_locations_should_accept_cell_instances(self):
        ws = Worksheet()
        ws.to_location = Mock(return_value=(1, 2))
        cell = Cell()

        ws[3, 4] = cell

        self.assertEquals(ws.to_location.call_args_list, [(((3, 4),), {})])
        self.assertEquals(ws.keys(), [(1, 2)])


    def test_setitem_on_locations_should_reject_non_cell_instances(self):
        ws = Worksheet()
        ws.to_location = Mock(return_value=(1, 2))

        expected_message_re = "^Worksheet locations must be Cell objects"
        with self.assertRaisesRegexp(TypeError, expected_message_re):
            ws[3, 4] = 123
        self.assertEquals(ws.to_location.call_args_list, [(((3, 4),), {})])


    def test_setitem_on_non_locations_raises_keyerror(self):
        ws = Worksheet()
        ws.to_location = Mock(return_value=None)

        with self.assertRaisesRegexp(InvalidKeyError, "^'random key' is not a valid cell location$"):
            ws['random key'] = 'sausages'


    def test_getitem_creates_cells(self):
        ws = Worksheet()
        try:
            ws[1, 2].value = Cell()
        except KeyError:
            self.fail('Did not create cell on request')


    def test_get_item_does_not_create_cells_for_random_strings(self):
        ws = Worksheet()
        with self.assertRaisesRegexp(InvalidKeyError, "^'name' is not a valid cell location$"):
            ws['name']
        with self.assertRaisesRegexp(AttributeError, "^'Worksheet' object has no attribute 'some_random_attribute'$"):
            ws.some_random_attribute


    def test_getitem_should_use_to_location_result_if_it_is_not_none(self):
        ws = Worksheet()
        ws.to_location = Mock(return_value=(1, 2))

        ws[3, 4].formula = "hello"

        self.assertEquals(ws.to_location.call_args_list, [(((3, 4),), {})])
        self.assertEquals(ws.keys(), [(1, 2)])
        self.assertEquals(ws.values()[0].formula, "hello")


    def test_getitem_should_use_original_key_if_to_location_gives_none(self):
        ws = Worksheet()
        ws.to_location = Mock(return_value=(3, 4))

        ws[3, 4].formula = "hello"

        self.assertEquals(ws.to_location.call_args_list, [(((3, 4),), {})])
        self.assertEquals(ws.keys(), [(3, 4)])
        self.assertEquals(ws.values()[0].formula, "hello")


    def test_getattr_should_delegate_to_getitem(self):
        ws = Worksheet()
        ws.__getitem__ = Mock()

        retval = ws.A1

        self.assertEquals( retval, ws.__getitem__.return_value )
        self.assertEquals( ws.__getitem__.call_args_list, [(('A1',), {})] )


    @patch('dirigible.sheet.worksheet.cell_name_to_coordinates')
    def test_setattr_should_delegate_to_setitem_if_attr_name_is_valid_cell_name(
        self, mock_name_to_coords
    ):
        def name_to_coords(name):
            if name == 'A1':
                return (2, 3)
            else:
                return None
        mock_name_to_coords.side_effect = name_to_coords

        ws = Worksheet()
        ws.__setitem__ = Mock()

        ws.A1 = 23

        self.assertEquals( ws.__setitem__.call_args_list, [(((2, 3), 23), {})] )


    @patch('dirigible.sheet.worksheet.cell_name_to_coordinates', lambda _: None)
    def test_setattr_should_not_delegate_to_setitem_if_attr_name_is_not_valid_cell_name(self):
        ws = Worksheet()
        ws.__setitem__ = Mock()

        ws.A1 = 23

        self.assertEquals( ws.__setitem__.call_args_list, [] )
        self.assertEquals( ws.A1, 23 )


    def test_set_cell_formula_with_value_should_update_internal_contents(self):
        ws = Worksheet()
        ws.set_cell_formula(1, 2, "3")
        self.assertEquals(ws[1, 2].formula, '3')


    def test_set_cell_formula_with_empty_string_should_clear_internal_contents_if_they_exist(self):
        ws = Worksheet()
        ws[1, 2].formula = "=1"
        ws.set_cell_formula(1, 2, "")
        self.assertFalse((1, 2) in ws)


    def test_set_cell_formula_with_empty_string_should_do_nothing_if_no_preexisting_internal_contents(self):
        ws = Worksheet()
        ws.set_cell_formula(1, 2, "")
        self.assertFalse((1, 2) in ws)


    def test_clear_values_clears_values_and_formatted_values_and_errors(self):
        ws = Worksheet()
        ws[1, 2].formula = "=1"
        ws[1, 2].python_formula = "2"
        ws[1, 2].value = "hello!"
        ws[1, 2].formatted_value = "Guten Tag!"
        ws[1, 2].error = "Goodness Gracious!"

        ws[2, 2].python_formula = "1 + 1"

        ws.clear_values()

        self.assertEquals(ws[1, 2].formula, "=1")
        self.assertEquals(ws[1, 2].python_formula, "2")
        self.assertEquals(ws[1, 2].value, undefined)
        self.assertEquals(ws[1, 2].formatted_value, u'')
        self.assertEquals(ws[1, 2].error, None)

        self.assertEquals(ws[2, 2].python_formula, '1 + 1')


    def test_clear_values_deletes_cells_with_no_formula(self):
        ws = Worksheet()
        ws[1, 2].formula = None
        ws[1, 2].value = "hello!"
        ws[1, 2].formatted_value = "Guten Tag!"
        ws.clear_values()
        self.assertFalse((1, 2) in ws)


    def test_clear_values_deletes_cells_with_empty_formula(self):
        ws = Worksheet()
        ws[1, 2].formula = ''
        ws[1, 2].value = "hello!"
        ws[1, 2].formatted_value = "Guten Tag!"
        ws.clear_values()
        self.assertFalse((1, 2) in ws)


    def test_iteration_yields_cells(self):
        ws = Worksheet()
        ws[1, 1].formula = 'A1'
        ws[2, 4].formula = 'B4'
        ws.name = 'any old name'

        self.assertEquals(ws.items(), [((1, 1), ws[1, 1]), ((2, 4), ws[2, 4])])


    def test_add_console_text_is_thread_safe(self):
        ws = Worksheet()
        num_threads = 100
        num_chars = 1000
        num_tries = 20

        def get_console_text_adder(char_num):
            def inner():
                for _ in range(num_tries):
                    ws.add_console_text(str(char_num) * num_chars)
            return inner
        threads = []
        for i in range(num_threads):
            threads.append(Thread(target=get_console_text_adder(i)))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        for i in range(num_threads):
            found_pos = -num_chars
            for _ in range(num_tries):
                found_pos = ws._console_text.find(str(i) * num_chars, found_pos + num_chars)
                self.assertNotEqual(found_pos, -1, 'could not find all output for thread %s' % (str(i),))


    def test_getting_bounds_on_empty_sheet_should_return_none(self):
        ws = Worksheet()
        self.assertEquals(ws.bounds, None)


    def test_getting_bounds_with_one_cell_should_return_bounds(self):
        ws = Worksheet()
        ws[3, 5].value = "Top right and bottom left!"

        self.assertEquals(type(ws.bounds), Bounds)
        self.assertEquals(ws.bounds, (3, 5, 3, 5))


    def test_getting_bounds_with_two_cells_should_return_bounds(self):
        ws = Worksheet()
        ws[5, 3].value = "Top right"
        ws[3, 11].value = "Bottom left"

        self.assertEquals(type(ws.bounds), Bounds)
        self.assertEquals(ws.bounds, (3, 3, 5, 11))


    def test_setting_bounds_should_fail(self):
        ws = Worksheet()
        with self.assertRaises(AttributeError):
            ws.bounds = Bounds((1, 2, 3, 4))



class TestWorksheetCellRangeConstructor(ResolverTestCase):

    def test_two_tuple_parameters(self):
        ws = Worksheet()
        cell_range = ws.cell_range((2, 3), (5, 4))
        self.assertEquals(cell_range.left, 2)
        self.assertEquals(cell_range.top, 3)
        self.assertEquals(cell_range.right, 5)
        self.assertEquals(cell_range.bottom, 4)

    def test_single_string_parameter_uses_formula_notation(self):
        ws = Worksheet()
        cell_range = ws.cell_range('A2:C4')
        self.assertEquals(cell_range.left, 1)
        self.assertEquals(cell_range.top, 2)
        self.assertEquals(cell_range.right, 3)
        self.assertEquals(cell_range.bottom, 4)

        try:
            _ = ws.cell_range('A1:wibble')
            self.fail('should raise ValueError')
        except ValueError, e:
            self.assertEquals(str(e), "Invalid cell range 'A1:wibble'")

        try:
            _ = ws.cell_range('wobblewibble')
            self.fail('should raise ValueError')
        except ValueError, e:
            self.assertEquals(str(e), "Invalid cell range 'wobblewibble'")


    def test_double_string_parameters_use_a1_notation(self):
        ws = Worksheet()
        cell_range = ws.cell_range('A2','C4')
        self.assertEquals(cell_range.left, 1)
        self.assertEquals(cell_range.top, 2)
        self.assertEquals(cell_range.right, 3)
        self.assertEquals(cell_range.bottom, 4)

        try:
            _ = ws.cell_range('wabble','C4')
            self.fail('should raise ValueError')
        except ValueError, e:
            self.assertEquals(str(e), "wabble is not a valid cell location")

        try:
            _ = ws.cell_range('A1','wooble')
            self.fail('should raise ValueError')
        except ValueError, e:
            self.assertEquals(str(e), "wooble is not a valid cell location")

        try:
            _ = ws.cell_range('weebble','beeble')
            self.fail('should raise ValueError')
        except ValueError, e:
            self.assertEquals(str(e), "Neither weebble nor beeble are valid cell locations")


    def test_mixed_parameters(self):
        ws = Worksheet()
        cell_range = ws.cell_range((10, 10),'C4')
        self.assertEquals(cell_range.left, 3)
        self.assertEquals(cell_range.top, 4)
        self.assertEquals(cell_range.right, 10)
        self.assertEquals(cell_range.bottom, 10)

        try:
            _ = ws.cell_range('wipple',(1,2))
            self.fail('should raise ValueError')
        except ValueError, e:
            self.assertEquals(str(e), "wipple is not a valid cell location")

        try:
            _ = ws.cell_range((2, 2),'wapple')
            self.fail('should raise ValueError')
        except ValueError, e:
            self.assertEquals(str(e), "wapple is not a valid cell location")



class BoundsTest(ResolverTestCase):

    def test_bounds_acts_like_tuple(self):
        bounds = Bounds((1, 2, 3, 4))
        self.assertTrue(isinstance(bounds, tuple))
        left, top, right, bottom = bounds
        self.assertEquals((left, top, right, bottom), (1, 2, 3, 4))


    def test_bounds_has_sweet_properties(self):
        bounds = Bounds((1, 2, 3, 4))
        self.assertEquals(bounds.left, 1)
        self.assertEquals(bounds.top, 2)
        self.assertEquals(bounds.right, 3)
        self.assertEquals(bounds.bottom, 4)


    def test_bounds_barfs_on_wrong_number_of_parameters(self):
        self.assertRaises(ValueError, lambda : Bounds((1, 2, 3)))
        self.assertRaises(ValueError, lambda : Bounds((1, 2, 3, 4, 5)))
