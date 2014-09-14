# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import with_statement

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock, patch, sentinel

from sheet.formula_interpreter import (
    get_dependencies_from_parse_tree, get_python_formula_from_parse_tree,
    rewrite
)
from sheet.parser import FormulaError
from sheet.parser.parse_node import ParseNode
from sheet.parser.parse_node_constructors import FLCellReference
from sheet.parser.parser import parse
from dirigible.test_utils import ResolverTestCase


class TestGetPythonFormulaFromParseTree(ResolverTestCase):

    @patch('sheet.formula_interpreter.rewrite')
    def test_flattens_rewrites_and_removes_1st_char(self, mock_rewrite):
        mock_rewrite.return_value = Mock()
        mock_rewrite.return_value.flatten.return_value = '123'

        result = get_python_formula_from_parse_tree(sentinel.parsed_formula)

        self.assertCalledOnce(mock_rewrite, sentinel.parsed_formula)
        self.assertCalledOnce(mock_rewrite.return_value.flatten)
        self.assertEquals(result, '23')


    def test_converts_formula_starting_with_equals(self):
        self.assertEquals(get_python_formula_from_parse_tree(parse('=1')), "1")
        self.assertEquals(get_python_formula_from_parse_tree(parse('=1+2')), "1+2")


    def test_converts_cell_references_and_adds_space(self):
        self.assertEquals(
            get_python_formula_from_parse_tree(parse('=A1')),
            "worksheet[(1,1)].value "
        )


    def test_produces_correct_python(self):
        self.assertEquals(
            get_python_formula_from_parse_tree(parse(
                '=[x * A1 for x in range(5)]'
            )),
            '[x * worksheet[(1,1)].value for x in range(5)]'
        )
        self.assertEquals(
            get_python_formula_from_parse_tree(parse(
                '=[x in A1:B3 for x in range(5)]'
            )),
            '[x in CellRange(worksheet,(1,1),(2,3)) for x in range(5)]'
        )
        self.assertEquals(
            get_python_formula_from_parse_tree(parse('={1 -> B1}')),
            '{1 :worksheet[(2,1)].value }'
        )
        self.assertEquals(
            get_python_formula_from_parse_tree(parse('=(lambda x -> C1 * x)(2)')),
            '(lambda x :worksheet[(3,1)].value * x)(2)'
        )



class TestRewrite(ResolverTestCase):

    def test_slicing_in_formulae(self):
        self.assertEquals(
            rewrite(parse('=p[1->]')).flatten(),
            '=p[1:]'
        )
        self.assertEquals(
            rewrite(parse('=p[->6]')).flatten(),
            '=p[:6]'
        )
        self.assertEquals(
            rewrite(parse('=p[1->6]')).flatten(),
            '=p[1:6]'
        )
        self.assertEquals(
            rewrite(parse('=p[1->6->3]')).flatten(),
            '=p[1:6:3]'
        )
        self.assertEquals(
            rewrite(parse('=p[1->->3]')).flatten(),
            '=p[1::3]'
        )


    def test_rewrite_string_should_return_object_unchanged(self):
        input = "Hello, world"
        self.assertEquals(rewrite(input), input)


    @patch('sheet.formula_interpreter.rewrite')
    def test_rewrite_parse_node_should_return_parse_node_with_children_rewritten(self, mock_recursive_rewrite):
        node_type = "junk node type"
        children = [ParseNode(node_type, None), ParseNode(node_type, None)]
        input = ParseNode(node_type, children)

        mock_recursive_results = [object(), object()]
        def mock_recursive_results_generator_func(*args):
            yield mock_recursive_results[0]
            yield mock_recursive_results[1]
        mock_recursive_results_generator = mock_recursive_results_generator_func()
        mock_recursive_rewrite.side_effect = lambda *_: mock_recursive_results_generator.next()

        self.assertEquals(id(rewrite(input)), id(input))
        self.assertEquals(
            mock_recursive_rewrite.call_args_list,
            [
                ((children[0],), {}),
                ((children[1],), {})
            ]
        )
        self.assertEquals(
            input.children,
            mock_recursive_results
        )


    def test_rewrite_cell_reference_should_return_appropriate_tree(self):
        self.assertEquals(
            rewrite(FLCellReference(["A2"])).flatten(),
            'worksheet[(1,2)].value '
        )


    def test_rewrite_should_translate_lambda_arrow_to_colon(self):
        self.assertEquals(
            rewrite(parse('=lambda x->  x')).flatten(),
            '=lambda x:x'
        )

        self.assertEquals(
            rewrite(parse('=lambda   x-> x')).flatten(),
            '=lambda   x:x'
            )

        self.assertEquals(
            rewrite(parse('=lambda x  -> x')).flatten(),
            '=lambda x  :x'
            )

        self.assertEquals(
            rewrite(parse('=lambda -> x')).flatten(),
            '=lambda :x'
            )


    def test_rewrite_should_translate_dictionary_arrow_to_colon(self):
        self.assertEquals(
            rewrite(parse('={"key"->"value"}')).flatten(),
            '={"key":"value"}'
            )

        self.assertEquals(
            rewrite(parse('={"key"  ->"value"}')).flatten(),
            '={"key"  :"value"}'
            )

        self.assertEquals(
            rewrite(parse('={"key"->  "value"}')).flatten(),
            '={"key":"value"}'
            )


    def test_rewrite_should_raise_invalid_cell_reference_error_when_appropriate(self):
        with self.assertRaises(FormulaError) as mgr:
            rewrite(parse('=#Invalid!')).flatten()
        self.assertEquals(str(mgr.exception), "#Invalid! cell reference in formula")

        with self.assertRaises(FormulaError) as mgr:
            rewrite(parse('=sum(#Invalid!:B1)'))
        self.assertEquals(str(mgr.exception), "#Invalid! cell reference in formula")


    def test_rewrite_should_raise_deleted_cell_reference_error_when_appropriate(self):
        with self.assertRaises(FormulaError) as mgr:
            rewrite(parse('=#Deleted!')).flatten()
        self.assertEquals(str(mgr.exception), "#Deleted! cell reference in formula")

        with self.assertRaises(FormulaError) as mgr:
            rewrite(parse('=sum(#Deleted!:B1)'))
        self.assertEquals(str(mgr.exception), "#Deleted! cell reference in formula")



class TestGetParseTreeDependencies(ResolverTestCase):

    def test_get_parse_tree_dependencies_should_return_empty_list_when_no_cell_refs(self):
        tree = parse("=1+2")
        self.assertEquals(get_dependencies_from_parse_tree(tree), [])


    def test_get_parse_tree_dependencies_should_return_locations_for_simple_expression(self):
        tree = parse("=a1+a2")
        self.assertEquals(get_dependencies_from_parse_tree(tree), [(1, 1), (1, 2)])


    def test_get_parse_tree_dependencies_should_return_locations_for_simple_expression_with_case_mismatch(self):
        tree = parse("=a1+A2")
        self.assertEquals(get_dependencies_from_parse_tree(tree), [(1, 1), (1, 2)])


    def test_get_parse_tree_dependencies_should_return_locations_disregarding_worksheet_names(self):
        tree = parse("=Sheet1!A3")
        self.assertEquals(get_dependencies_from_parse_tree(tree), [(1, 3)])


    def test_get_parse_tree_dependencies_should_return_locations_used_for_function_calls_and_arguments(self):
        tree = parse("=A2(a3)")
        self.assertEquals(get_dependencies_from_parse_tree(tree), [(1, 2), (1, 3)])


    def test_get_parse_tree_dependencies_should_not_return_locations_for_invalid_references(self):
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Invalid!")), [])
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Invalid! + A2")), [(1, 2)])


    def test_get_parse_tree_dependencies_should_not_return_locations_for_deleted_references(self):
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Deleted!")), [])
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Deleted! + A2")), [(1, 2)])


    def test_get_parse_tree_dependencies_should_not_return_locations_for_invalid_references_in_cell_ranges(self):
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Invalid!:A2")), [])
        self.assertEquals(get_dependencies_from_parse_tree(parse("=A2:#Invalid!")), [])
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Invalid!:#Invalid!")), [])


    def test_get_parse_tree_dependencies_should_not_return_locations_for_deleted_references_in_cell_ranges(self):
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Deleted!:A2")), [])
        self.assertEquals(get_dependencies_from_parse_tree(parse("=A2:#Deleted!")), [])
        self.assertEquals(get_dependencies_from_parse_tree(parse("=#Deleted!:#Deleted!")), [])


    def test_get_parse_tree_dependencies_should_not_return_locations_for_worksheet_references(self):
        for expression in ("=<Sheet1>", "=<Sheet1>.Bounds", "=<Sheet1> + <Sheet2>"):
            self.assertEquals(get_dependencies_from_parse_tree(parse(expression)), [])
        self.assertEquals(get_dependencies_from_parse_tree(parse("=<Sheet1> + A2")), [(1, 2)])


    def test_get_parse_tree_dependencies_should_return_cellrange_deps(self):
        self.assertItemsEqual(
            get_dependencies_from_parse_tree(parse('=a2:b3')),
            [(1, 2), (1, 3), (2, 2), (2, 3)]
        )
        self.assertItemsEqual(
            get_dependencies_from_parse_tree(parse('=b3:a2')),
            [(1, 2), (1, 3), (2, 2), (2, 3)]
        )
        self.assertItemsEqual(
            get_dependencies_from_parse_tree(parse('=a3:b2')),
            [(1, 2), (1, 3), (2, 2), (2, 3)]
        )


