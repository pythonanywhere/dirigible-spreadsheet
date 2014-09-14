# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
try:
    import simplejson as json
except ImportError:
    import json

from mock import Mock, patch

from django.contrib.auth.models import User

from test_utils import ResolverTestCase

from sheet.models import Clipboard, Sheet
from sheet.worksheet import Cell, Worksheet


class ClipboardModelTest(ResolverTestCase):

    def test_initial_fields(self):
        user = User()
        user.username = 'testuser'
        clipboard = Clipboard(owner=user)
        self.assertEquals(clipboard.owner,  user)
        self.assertEquals(clipboard.contents_json, '{}')
        self.assertEquals(clipboard.is_cut, False)
        self.assertEquals(clipboard.source_left, None)
        self.assertEquals(clipboard.source_top, None)
        self.assertEquals(clipboard.source_right, None)
        self.assertEquals(clipboard.source_bottom, None)
        self.assertEquals(clipboard.source_sheet, None)


    def test_source_range(self):
        user = User()
        user.username = 'testuser'
        clipboard = Clipboard(owner=user)
        clipboard.source_left = 1
        clipboard.source_top = 2
        clipboard.source_right = 3
        clipboard.source_bottom = 4
        self.assertEquals(clipboard.source_range, (1, 2, 3, 4))

    def test_width_and_height(self):
        user = User()
        user.username = 'testuser'
        clipboard = Clipboard(owner=user)
        clipboard.source_left = 1
        clipboard.source_top = 2
        clipboard.source_right = 3
        clipboard.source_bottom = 5
        self.assertEquals(clipboard.width, 3)
        self.assertEquals(clipboard.height, 4)


    def test_clipboad_copy_retrieves_stuff_from_sheet_and_removes_offset(self):
        self.maxDiff = None
        clipboard = Clipboard()
        sheet = Sheet()
        worksheet = Worksheet()
        worksheet.C2.formula = 'foo'
        worksheet.C2.formatted_value = 'fv'
        worksheet.D2.formatted_value = 'fv to become formula'

        sheet.jsonify_worksheet(worksheet)
        start = (3, 2)
        end = (4, 3)
        cut_called_previously = True
        clipboard.is_cut = cut_called_previously
        clipboard.copy(sheet, start, end)
        self.assertEquals(
            json.loads(clipboard.contents_json),
            {
                '0,0':{'formula': 'foo',
                    'formatted_value': 'fv'},
                '1,0':{'formula': 'fv to become formula',
                    'formatted_value': 'fv to become formula'},
                '0,1':{'formula': '',
                    'formatted_value': ''},
                '1,1':{'formula': '',
                    'formatted_value': ''}
            }
        )
        self.assertEquals(clipboard.source_left, 3)
        self.assertEquals(clipboard.source_top, 2)
        self.assertEquals(clipboard.source_right, 4)
        self.assertEquals(clipboard.source_bottom, 3)

        self.assertEquals(clipboard.is_cut, False)
        self.assertEquals(clipboard.source_sheet, None)


    def test_cut_calls_copy_then_cuts_and_remembers_some_stuff(self):
        clipboard = Clipboard()
        sheet = Sheet()
        user = User()
        user.username = 'test_cuttter'
        user.save()
        sheet.owner = user
        clipboard.copy = Mock(wraps=clipboard.copy)

        worksheet = Worksheet()
        worksheet.A1.formula = 'outside'
        worksheet.A2.formula = 'inside'
        sheet.jsonify_worksheet(worksheet)
        sheet.save()

        clipboard.cut(sheet, (1, 2), (3, 4))

        self.assertCalledOnce(clipboard.copy, sheet, (1, 2), (3, 4))

        worksheet = sheet.unjsonify_worksheet()

        self.assertEquals(worksheet.A1.formula, 'outside')
        self.assertEquals(worksheet.A2, Cell())

        self.assertEquals(clipboard.source_left, 1)
        self.assertEquals(clipboard.source_top, 2)
        self.assertEquals(clipboard.source_right, 3)
        self.assertEquals(clipboard.source_bottom, 4)

        self.assertEquals(clipboard.is_cut, True)
        self.assertEquals(clipboard.source_sheet, sheet)


    @patch('dirigible.sheet.clipboard.StringIO')
    def test_clipboard_remembers_to_close_stingIO_stream(self, mock_stringio):
        sheet = Sheet()
        clipboard = Clipboard()
        mock_stringio.StringIO.return_value = Mock()
        clipboard.copy(sheet, (1, 1), (1, 1))
        self.assertCalledOnce(mock_stringio.StringIO.return_value.close)


    def test_clipboard_json_to_cells(self):
        self.maxDiff = None
        clipboard = Clipboard()
        clipboard.source_left = 1
        clipboard.source_top = 2
        clipboard.source_right = 2
        clipboard.source_bottom = 3
        strings_dict = {
                '0,0':{'formula': 'foo',
                    'formatted_value': 'fv'},
                '1,0':{'formula': 'fv to become formula',
                    'formatted_value': 'fv to become formula'},
                '0,1':{'formula': '',
                    'formatted_value': ''},
                '1,1':{'formula': '',
                    'formatted_value': ''}
            }
        clipboard.contents_json = json.dumps(strings_dict)

        c2 = Cell()
        c2.formula = 'foo'
        c2.formatted_value = 'fv'
        d2 = Cell()
        d2.formula = 'fv to become formula'
        d2.formatted_value = d2.formula
        c3 = Cell()
        d3 = Cell()
        expected_cells = {
            (0, 0): c2,
            (0, 1): c3,
            (1, 0): d2,
            (1, 1): d3,
        }

        self.assertEquals(dict(clipboard.to_cells((0, 0), (1, 1))), expected_cells)


    def test_paste_to_for_copy(self):
        c2 = Cell()
        c2.formula = 'foo'
        c2.formatted_value = 'fv'
        d2 = Cell()
        d2.formula = 'fv to become formula'
        d2.formatted_value = d2.formula
        c3 = Cell()
        d3 = Cell()
        cells = {
            (2, 2): c2,
            (2, 3): c3,
            (3, 2): d2,
            (3, 3): d3,
        }

        clipboard = Clipboard()
        clipboard.source_left = 1
        clipboard.source_top = 1
        clipboard.source_right = 2
        clipboard.source_bottom = 2
        clipboard.to_cells = Mock()
        clipboard.to_cells.return_value = cells.iteritems()

        sheet = Sheet()
        worksheet = Worksheet()
        worksheet.B3.formula = 'i am in danger!'
        worksheet.A1.formula = 'i am safe :-)'
        sheet.jsonify_worksheet(worksheet)

        clipboard.paste_to(sheet, (2, 2), (2, 2))

        updated_worksheet = sheet.unjsonify_worksheet()
        self.assertEquals(updated_worksheet.A1.formula, 'i am safe :-)')
        self.assertEquals(updated_worksheet.B2.formula, c2.formula)
        self.assertEquals(updated_worksheet.C2.formula, d2.formula)
        self.assertEquals(updated_worksheet.B3.formula, c3.formula)
        self.assertEquals(updated_worksheet.C3.formula, d3.formula)


    def test_paste_to_for_cut_different_sheet(self):
        self.user = User()
        self.user.save()

        c2 = Cell()
        c2.formula = 'foo'
        c2.formatted_value = 'fv'
        d2 = Cell()
        d2.formula = 'fv to become formula'
        d2.formatted_value = d2.formula
        c3 = Cell()
        d3 = Cell()
        c5 = Cell()
        c5.formula = 'a safe source cell'
        dest_cells = {
            (3, 4): c2,
            (3, 5): c3,
            (4, 4): d2,
            (4, 5): d3,
        }

        source_sheet = Sheet()
        source_sheet.owner = self.user
        source_sheet.save()

        clipboard = Clipboard()
        clipboard.to_cells = Mock()
        clipboard.to_cells.return_value = dest_cells.iteritems()
        clipboard.is_cut = True
        clipboard.source_sheet = source_sheet
        clipboard.source_left = 3
        clipboard.source_top = 2
        clipboard.source_right = 4
        clipboard.source_bottom = 3

        destination_sheet = Sheet()
        destination_sheet.owner = self.user
        destination_worksheet = Worksheet()
        destination_worksheet.C4.formula = 'i am in danger!'
        destination_worksheet.A1.formula = 'i am safe :-)'
        destination_sheet.jsonify_worksheet(destination_worksheet)
        destination_sheet.save()

        clipboard.paste_to(destination_sheet, (3, 4), (3, 4))

        updated_worksheet = destination_sheet.unjsonify_worksheet()
        self.assertEquals(updated_worksheet.A1.formula, 'i am safe :-)')
        self.assertEquals(updated_worksheet.C4.formula, c2.formula)
        self.assertEquals(updated_worksheet.D4.formula, d2.formula)
        self.assertEquals(updated_worksheet.C5.formula, c3.formula)
        self.assertEquals(updated_worksheet.d5.formula, d3.formula)

        # paste should reset the clipboard so that future pastes act as
        # though they came from a copy
        self.assertEquals(clipboard.source_left, 3)
        self.assertEquals(clipboard.source_top, 4)
        self.assertEquals(clipboard.source_right, 4)
        self.assertEquals(clipboard.source_bottom, 5)
        self.assertEquals(clipboard.is_cut, False)
        self.assertEquals(clipboard.source_sheet, None)


    def test_copy_then_paste_same_sheet(self):
        sheet = Sheet()
        worksheet = Worksheet()
        worksheet.A1.formula = 'safe'
        worksheet.A2.formula = 'topleft'
        worksheet.B2.formula = 'topright'
        worksheet.A3.formula = 'bottomleft'
        worksheet.B3.formula = 'bottomright'
        sheet.jsonify_worksheet(worksheet)

        clipboard = Clipboard()
        clipboard.copy(sheet, (1, 2), (2, 3))
        clipboard.paste_to(sheet, (2, 3), (2, 3))

        updated_worksheet = sheet.unjsonify_worksheet()
        self.assertEquals(updated_worksheet.A1.formula, 'safe')
        self.assertEquals(updated_worksheet.A2.formula, 'topleft')
        self.assertEquals(updated_worksheet.B2.formula, 'topright')
        self.assertEquals(updated_worksheet.A3.formula, 'bottomleft')
        self.assertEquals(updated_worksheet.C3.formula, 'topright')
        self.assertEquals(updated_worksheet.C4.formula, 'bottomright')
        self.assertEquals(updated_worksheet.B4.formula, 'bottomleft')
        self.assertEquals(updated_worksheet.B3.formula, 'topleft')


    def test_cut_then_paste_same_sheet(self):
        sheet = Sheet()
        worksheet = Worksheet()
        worksheet.A1.formula = 'safe'
        worksheet.A2.formula = 'topleft'
        worksheet.B2.formula = 'topright'
        worksheet.A3.formula = 'bottomleft'
        worksheet.B3.formula = 'bottomright'
        sheet.jsonify_worksheet(worksheet)

        clipboard = Clipboard()
        clipboard.cut(sheet, (1, 2), (2, 3))

        updated_worksheet = sheet.unjsonify_worksheet()
        self.assertEquals(updated_worksheet.A1.formula, 'safe')
        self.assertEquals(updated_worksheet.A2, Cell() )
        self.assertEquals(updated_worksheet.B2, Cell() )
        self.assertEquals(updated_worksheet.A3, Cell() )

        clipboard.paste_to(sheet, (2, 3), (2, 3))

        updated_worksheet = sheet.unjsonify_worksheet()

        self.assertEquals(updated_worksheet.A1.formula, 'safe')
        self.assertEquals(updated_worksheet.A2, Cell() )
        self.assertEquals(updated_worksheet.B2, Cell() )
        self.assertEquals(updated_worksheet.A3, Cell() )
        self.assertEquals(updated_worksheet.B3.formula, 'topleft')
        self.assertEquals(updated_worksheet.C3.formula, 'topright')
        self.assertEquals(updated_worksheet.C4.formula, 'bottomright')
        self.assertEquals(updated_worksheet.B4.formula, 'bottomleft')


    def test_paste_to_should_tile_clipboard_contents_across_selected_range(self):
        sheet = Sheet()
        worksheet = Worksheet()
        worksheet.A1.formula = '=c1'
        worksheet.B1.formula = '=d1'
        worksheet.A2.formula = '=c2'
        worksheet.B2.formula = '=d2'
        sheet.jsonify_worksheet(worksheet)

        clipboard = Clipboard()
        clipboard.copy(sheet, (1, 1), (2, 2))
        clipboard.paste_to(sheet, (3, 3), (5, 7))

        worksheet = sheet.unjsonify_worksheet()
        self.assertEquals(worksheet.C3.formula, '=E3')
        self.assertEquals(worksheet.D3.formula, '=F3')
        self.assertEquals(worksheet.E3.formula, '=G3')
        self.assertEquals(worksheet.F3.formula, None)

        self.assertEquals(worksheet.C4.formula, '=E4')
        self.assertEquals(worksheet.D4.formula, '=F4')
        self.assertEquals(worksheet.E4.formula, '=G4')
        self.assertEquals(worksheet.F4.formula, None)

        self.assertEquals(worksheet.C5.formula, '=E5')
        self.assertEquals(worksheet.D5.formula, '=F5')
        self.assertEquals(worksheet.E5.formula, '=G5')
        self.assertEquals(worksheet.F5.formula, None)

        self.assertEquals(worksheet.C6.formula, '=E6')
        self.assertEquals(worksheet.D6.formula, '=F6')
        self.assertEquals(worksheet.E6.formula, '=G6')
        self.assertEquals(worksheet.F6.formula, None)

        self.assertEquals(worksheet.C7.formula, '=E7')
        self.assertEquals(worksheet.D7.formula, '=F7')
        self.assertEquals(worksheet.E7.formula, '=G7')
        self.assertEquals(worksheet.F7.formula, None)

        self.assertEquals(worksheet.C8.formula, None)
        self.assertEquals(worksheet.D8.formula, None)
        self.assertEquals(worksheet.E8.formula, None)
        self.assertEquals(worksheet.F8.formula, None)


class FormulaRewriteTest(ResolverTestCase):

    @patch('dirigible.sheet.clipboard.rewrite_formula')
    def test_formulae_are_rewritten(self, mock_rewrite):
        mock_rewrite.return_value = '=C8'

        sheet = Sheet()
        worksheet = Worksheet()
        worksheet.A1.formula = '=B6'
        sheet.jsonify_worksheet(worksheet)
        clipboard = Clipboard()
        clipboard.copy(sheet, (1, 1), (1, 1))

        clipboard.paste_to(sheet, (2, 3), (2, 3))

        self.assertCalledOnce(
            mock_rewrite,
            '=B6', 1, 2, False, (1, 1, 1, 1)
        )


    @patch('dirigible.sheet.clipboard.rewrite_source_sheet_formulae_for_cut')
    def test_paste_from_cut_rewrites_source_worksheet_formulae_before_pasting(
            self, mock_rewrite_source_sheet_formulae):
        source_worksheet = Worksheet()
        source_worksheet.A1.formula = '=pre-rewrite'
        source_sheet = Sheet()
        source_sheet.jsonify_worksheet(source_worksheet)

        clipboard = Clipboard()
        clipboard.cut(source_sheet, (1, 2), (3, 5))
        clipboard.to_cells = Mock()
        clipboard.to_cells.return_value = {}.items()

        def check_to_cells_not_run(*args):
            self.assertFalse(clipboard.to_cells.call_args_list)

        mock_rewrite_source_sheet_formulae.side_effect = check_to_cells_not_run

        clipboard.paste_to(source_sheet, (2, 3), (2, 3))

        self.assertCalledOnce(
            mock_rewrite_source_sheet_formulae,
            source_worksheet, (1, 2, 3, 5), 2, 3
        )


    @patch('dirigible.sheet.clipboard.rewrite_source_sheet_formulae_for_cut')
    def test_paste_from_copy_does_not_rewrite_source_sheet_formulae(
            self, mock_rewrite_source_sheet_formulae):
        source_worksheet = Worksheet()
        source_worksheet.A1.formula = '=pre-rewrite'
        source_sheet = Sheet()
        source_sheet.jsonify_worksheet(source_worksheet)

        clipboard = Clipboard()
        clipboard.copy(source_sheet, (1, 2), (3, 5))
        clipboard.to_cells = Mock()
        clipboard.to_cells.return_value = {}.items()

        def check_to_cells_not_run(*args):
            self.assertFalse(clipboard.to_cells.call_args_list)

        mock_rewrite_source_sheet_formulae.side_effect = check_to_cells_not_run

        clipboard.paste_to(source_sheet, (2, 3), (2, 3))

        self.assertFalse( mock_rewrite_source_sheet_formulae.called )


    @patch('dirigible.sheet.clipboard.rewrite_source_sheet_formulae_for_cut')
    def test_paste_onto_different_sheet_from_cut_does_not_rewrite_source_sheet_formulae(
            self, mock_rewrite_source_sheet_formulae
        ):
        source_worksheet = Worksheet()
        source_worksheet.A1.formula = '=pre-rewrite'
        source_sheet = Sheet()
        source_sheet.jsonify_worksheet(source_worksheet)

        dest_sheet = Mock()

        clipboard = Clipboard()
        clipboard.cut(source_sheet, (1, 2), (3, 5))
        clipboard.to_cells = Mock()
        clipboard.to_cells.return_value = {}.items()

        def check_to_cells_not_run(*args):
            self.assertFalse(clipboard.to_cells.call_args_list)

        mock_rewrite_source_sheet_formulae.side_effect = check_to_cells_not_run

        clipboard.paste_to(dest_sheet, (2, 3), (2, 3))

        self.assertFalse( mock_rewrite_source_sheet_formulae.called )


