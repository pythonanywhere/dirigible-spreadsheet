# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import with_statement

try:
    import unittest2 as unittest
except ImportError:
    import unittest
from mock import Mock, patch, sentinel

from sheet.cell import Cell, undefined
from sheet.worksheet import Worksheet
from dirigible.test_utils import ResolverTestCase


class TestUndefined(unittest.TestCase):

    def test_repr(self):
        self.assertEquals(repr(undefined), "<undefined>")



class TestCell(ResolverTestCase):

    def test_initialisation(self):
        self.assertEquals(Cell().formula, None)
        self.assertEquals(Cell().python_formula, None)
        self.assertEquals(Cell().dependencies, [])
        self.assertEquals(Cell().value, undefined)
        self.assertEquals(Cell().formatted_value, u'')
        self.assertEquals(Cell().error, None)


    def test_clear_value_clears_value_but_not_formatted_value(self):
        cell = Cell()

        cell.value = 29
        cell.formatted_value = "wibble"

        cell.clear_value()

        self.assertEquals(cell.value, undefined)
        self.assertEquals(cell.formatted_value, "wibble")


    def test_clear_clears_stuff(self):
        cell = Cell()

        cell.value = 29
        cell.formula = 'e equals emcee squared'
        cell.python_formula = 'e equals emcee squared'
        cell.dependencies = [(1, 1), (2, 2)]
        cell.formatted_value = "wibble"
        cell.error = 'a spear'

        cell.clear()

        self.assertEquals(cell.value, undefined)
        self.assertEquals(cell.formula, None)
        self.assertEquals(cell.python_formula, None)
        self.assertEquals(Cell().dependencies, [])
        self.assertEquals(cell.formatted_value, u"")
        self.assertEquals(cell.error, None)


    def test_setting_value_to_ws_doesnt_die(self):
        # This is actually mostly testing that it doesn't explode
        cell = Cell()
        ws = Worksheet()
        cell.value = ws
        self.assertEquals(cell.formatted_value, unicode(ws))


    def test_setting_value_to_undefined_sets_formatted_value_to_empty_string(self):
        cell = Cell()
        cell._set_formatted_value = Mock()
        cell.value = undefined
        self.assertCalledOnce(cell._set_formatted_value, u'')

    def test_setting_value_sets_formatted_value_to_unicode_version(self):
        cell = Cell()
        cell._set_formatted_value = Mock()
        cell.value = sentinel.value
        self.assertCalledOnce(cell._set_formatted_value, unicode(sentinel.value))


    def test_setting_formatted_value_to_string_passes_through(self):
        cell = Cell()
        cell.formatted_value = 'this > string'
        self.assertEquals(cell.formatted_value, 'this > string')


    def test_setting_formatted_value_to_non_string_explodes(self):
        class TestObject(object):
            pass
        cell = Cell()

        with self.assertRaises(TypeError) as mngr:
            cell.formatted_value = TestObject()
        self.assertEquals(str(mngr.exception), 'cell formatted_value must be str or unicode')


    def test_setting_formatted_value_to_none(self):
        cell = Cell()
        cell.formatted_value = None
        self.assertEquals(cell.formatted_value, '')


    def test_setting_formatted_value_to_unicode(self):
        cell = Cell()
        cell.formatted_value = u'Sacr\xe9 bleu!'
        self.assertEquals(cell.formatted_value, u'Sacr\xe9 bleu!')


    def test_setting_formula_to_string_passes_through(self):
        cell = Cell()
        cell.formula = 'this < string'
        self.assertEquals(cell.formula, 'this < string')


    def test_setting_formula_to_non_string_explodes(self):
        class TestObject(object):
            pass
        cell = Cell()

        with self.assertRaises(TypeError) as mngr:
            cell.formula = TestObject()
        self.assertEquals(str(mngr.exception), 'cell formula must be str or unicode')


    def test_setting_formula_to_none_works_and_sets_python_formula_to_none(self):
        cell = Cell()
        cell.python_formula = 'something'

        cell.formula = None

        self.assertEquals(cell.formula, None)
        self.assertEquals(cell.python_formula, None)


    def test_setting_formula_to_constant_clears_python_formula(self):
        cell = Cell()
        cell.python_formula = 'something'

        cell.formula = 'k'

        self.assertEquals(cell.python_formula, None)


    @patch('sheet.cell.get_dependencies_from_parse_tree')
    @patch('sheet.cell.get_python_formula_from_parse_tree')
    @patch('sheet.cell.parser')
    def test_setting_formula_parses_formula_sets_dependencies_then_sets_python_formula(
            self, mock_parser, mock_get_python_formula_from_parse_tree, mock_get_dependencies_from_parse_tree
    ):
        call_order = []
        def get_add_call(name, return_value):
            def add_call(*_):
                call_order.append(name)
                return return_value
            return add_call
        mock_get_python_formula_from_parse_tree.side_effect = get_add_call('formula', sentinel.formula)
        mock_get_dependencies_from_parse_tree.side_effect = get_add_call('dependencies', sentinel.dependencies)

        cell = Cell()
        cell.python_formula = '=something'

        cell.formula = '=k'

        self.assertCalledOnce(mock_parser.parse, '=k')

        self.assertCalledOnce(mock_get_python_formula_from_parse_tree,
            mock_parser.parse.return_value
        )
        self.assertEquals(
            cell._python_formula,
            sentinel.formula
        )

        self.assertCalledOnce(mock_get_dependencies_from_parse_tree,
            mock_parser.parse.return_value
        )
        self.assertEquals(
            cell.dependencies,
            sentinel.dependencies
        )

        self.assertEquals(call_order, ['dependencies', 'formula'])


    def test_setting_formula_with_syntax_error_sets_appropriate_raise_in_python_formula_and_clears_dependencies(self):
        cell = Cell()

        cell.dependencies = 'before'
        cell.python_formula = 'before'
        cell.formula = '=#NULL!'
        self.assertEquals(
            cell.python_formula,
            '_raise(FormulaError("Error in formula at position 2: unexpected \'#NULL!\'"))'
        )
        self.assertEquals(cell.dependencies, [])

        cell.dependencies = 'before'
        cell.python_formula = 'before'
        cell.formula = '=#Invalid!'
        self.assertEquals(
            cell.python_formula,
            '_raise(FormulaError("#Invalid! cell reference in formula"))'
        )
        self.assertEquals(cell.dependencies, [])

        cell.dependencies = 'before'
        cell.python_formula = 'before'
        cell.formula = '=#Deleted!'
        self.assertEquals(
            cell.python_formula,
            '_raise(FormulaError("#Deleted! cell reference in formula"))'
        )
        self.assertEquals(cell.dependencies, [])


    def test_setting_python_formula_to_non_string_explodes(self):
        cell = Cell()

        with self.assertRaises(TypeError) as mngr:
            cell.python_formula = type

        self.assertEquals(
                str(mngr.exception),
                'cell python_formula must be str or unicode'
        )


    def test_can_use_unicode_in_formula(self):
        cell = Cell()
        cell.formula = u'Sacr\xe9 bleu!'
        self.assertEquals(cell.formula, u'Sacr\xe9 bleu!')


    def test_repr(self):
        cell = Cell()
        cell.formula = 'f'
        self.assertEquals(repr(cell), "<Cell formula=f value=<undefined> formatted_value=u''>")

        cell = Cell()
        cell.value = 'v'
        self.assertEquals(repr(cell), "<Cell formula=None value='v' formatted_value=u'v'>")

        cell = Cell()
        cell.value = 23
        self.assertEquals(repr(cell), "<Cell formula=None value=23 formatted_value=u'23'>")

        cell = Cell()
        cell.formula = 'f'
        cell.value = 'v'
        self.assertEquals(repr(cell), "<Cell formula=f value='v' formatted_value=u'v'>")

        cell = Cell()
        cell.formula = 'f'
        cell.value = 'v'
        cell.formatted_value = u'fv'
        self.assertEquals(repr(cell), "<Cell formula=f value='v' formatted_value=u'fv'>")

        cell = Cell()
        cell.formula = 'f'
        cell.value = 'v'
        cell.formatted_value = u'fv'
        cell.error = 'e'
        self.assertEquals(repr(cell), "<Cell formula=f value='v' formatted_value=u'fv' error='e'>")


    def test_eq_neq(self):
        cell1 = Cell()
        cell1.formula = '=formula'
        cell2 = Cell()
        cell2.formula = '=formula'
        self.assertTrue(cell1 == cell2)
        self.assertFalse(cell1 != cell2)

        cell1.value = 10
        self.assertFalse(cell1 == cell2)
        self.assertTrue(cell1 != cell2)
        cell2.value = 10
        self.assertTrue(cell1 == cell2)
        self.assertFalse(cell1 != cell2)

        cell1.formatted_value = 'formatted'
        self.assertFalse(cell1 == cell2)
        self.assertTrue(cell1 != cell2)
        cell2.formatted_value = 'formatted'
        self.assertTrue(cell1 == cell2)
        self.assertFalse(cell1 != cell2)

        cell1.error = 'this error'
        self.assertFalse(cell1 == cell2)
        self.assertTrue(cell1 != cell2)
        cell2.error = 'this error'
        self.assertTrue(cell1 == cell2)
        self.assertFalse(cell1 != cell2)

        self.assertFalse(cell1 == 'hello')
        self.assertTrue(cell1 != 'hello')
