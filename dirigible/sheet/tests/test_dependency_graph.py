# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#


from mock import call, Mock, patch, sentinel

from dirigible.test_utils import die, ResolverTestCase

from sheet.cell import Cell
from sheet.dependency_graph import (
    _add_location_dependencies, build_dependency_graph,
    _generate_cell_subgraph, Node)
from sheet.errors import (
    CycleError, report_cell_error,
)
from sheet.worksheet import Worksheet


class TestBuildDependencyGraph(ResolverTestCase):

    def test_returns_graph_and_leaf_nodes(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = '=A2 + B2'
        worksheet[1, 2].formula = '=A3'
        worksheet[2, 2].formula = '=B3'
        worksheet[1, 3].formula = '=1'
        worksheet[2, 3].formula = '1'
        worksheet[3, 3].python_formula = '1'

        graph, leaves = build_dependency_graph(worksheet)

        self.maxDiff = None
        self.assertEquals(
            graph,
            {
                (1, 1): Node(
                    (1, 1),
                    children=set([(1, 2), (2, 2)]),
                    parents=set()
                ),
                (1, 2): Node(
                    (1, 2),
                    children=set([(1, 3)]),
                    parents=set([(1, 1)])
                ),
                (2, 2): Node(
                    (2, 2),
                    children=set(),
                    parents=set([(1, 1)])
                ),
                (1, 3): Node(
                    (1, 3),
                    children=set(),
                    parents=set([(1, 2)])
                ),
                (3, 3): Node(
                    (3, 3),
                    children=set(),
                    parents=set()
                ),
            }
        )
        self.assertEquals(set(leaves), set([(1, 3), (2, 2), (3, 3)]))

        worksheet[1, 2].formula = '=A3 + B3'
        graph, leaves = build_dependency_graph(worksheet)

        self.assertEquals(graph, {
            (1, 1): Node(
                (1, 1),
                children=set([(1, 2), (2, 2)]),
                parents=set(),
            ),
            (1, 2): Node(
                (1, 2),
                children=set([(1, 3)]),
                parents=set([(1, 1)]),
            ),
            (2, 2): Node(
                (2, 2),
                children=set(),
                parents=set([(1, 1)])
            ),
            (1, 3): Node(
                (1, 3),
                children=set(),
                parents=set([(1, 2)])
            ),
            (3, 3): Node(
                (3, 3),
                children=set(),
                parents=set()
            ),
        })
        self.assertEquals(set(leaves), set([(1, 3), (2, 2), (3, 3)]))


    def test_is_robust_against_references_to_empty_cells(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = '=A2'

        # NB we're making sure that this call doesn't raise an error
        # because the cell A2 is created in the dictionary while we're
        # iterating over it.
        graph, leaves = build_dependency_graph(worksheet)

        self.maxDiff = None
        self.assertEquals(
            graph,
            {
                (1, 1): Node(
                    (1, 1),
                    children=set(),
                    parents=set()
                )
            }
        )
        self.assertEquals(leaves, [(1, 1)])


    @patch('sheet.dependency_graph.report_cell_error')
    def test_puts_errors_on_cells_in_cycles_and_omits_them_from_graph(self, mock_report_cell_error):
        mock_report_cell_error.side_effect = report_cell_error
        worksheet = Worksheet()
        worksheet[1, 1].formula = '=A2'
        worksheet[1, 2].formula = '=A1'
        worksheet[1, 3].formula = '=A1'
        worksheet[1, 4].formula = '=A5'
        worksheet[1, 5].formula = '=5'

        graph, leaves = build_dependency_graph(worksheet)
        self.assertEquals(
            graph,
            {
                (1, 3): Node((1, 3), children=set(), parents=set()),
                (1, 4): Node((1, 4), children=set([(1, 5)]), parents=set()),
                (1, 5): Node((1, 5), children=set(), parents=set([(1, 4)])),
            }
        )
        self.assertEquals(leaves, [(1, 5), (1, 3)])
        a1_cycle_error = CycleError([(1, 2), (1, 1), (1, 2)])
        self.assertEquals(
            mock_report_cell_error.call_args_list,
            [
                call(worksheet, (1, 2), a1_cycle_error),
                call(worksheet, (1, 1), a1_cycle_error),
            ]
        )


class TestGenerateCellSubgraph(ResolverTestCase):

    @patch('sheet.dependency_graph._generate_cell_subgraph')
    @patch('sheet.dependency_graph._add_location_dependencies')
    def test_should_recursively_call_itself_on_dependencies_before_adding_dependencies_to_graph(
        self, mock_add_location_dependencies, mock_generate_cell_subgraph
    ):
        mock_generate_cell_subgraph.copied_call_args_list = []

        def mock_recalc_recursive_call(worksheet, context, loc, visited, path):
            self.assertFalse(mock_add_location_dependencies.called)
            mock_generate_cell_subgraph.copied_call_args_list.append((worksheet, context, loc, set(visited), list(path)))


        mock_generate_cell_subgraph.side_effect = mock_recalc_recursive_call
        mock_generate_cell_subgraph_was_called_before_add_location_dependencies = []

        def add_location_dependencies_side_effect(*_):
            mock_generate_cell_subgraph_was_called_before_add_location_dependencies.append(mock_generate_cell_subgraph.called)
        mock_add_location_dependencies.side_effect = add_location_dependencies_side_effect

        worksheet = Worksheet()
        worksheet[1, 11].formula = '=formula'
        worksheet[1, 11].dependencies = [(2, 22), (3, 33)]
        context = sentinel.context

        _generate_cell_subgraph(worksheet, context, (1, 11), set(), [])

        self.assertTrue(mock_add_location_dependencies.called)
        self.assertTrue(mock_generate_cell_subgraph_was_called_before_add_location_dependencies[0])
        self.assertItemsEqual(
            mock_generate_cell_subgraph.copied_call_args_list,
            [
                (worksheet, context, (2, 22), set(), [(1, 11)]),
                (worksheet, context, (3, 33), set(), [(1, 11)]),
            ]
        )


    @patch('sheet.dependency_graph._add_location_dependencies')
    def test_should_add_dependencies_to_graph(
        self, mock_add_location_dependencies
    ):
        worksheet = Worksheet()
        worksheet[99, 98].formula = '=foobar'
        worksheet[1, 11].formula = '=foo'
        worksheet[1, 11].dependencies = [(99, 98)]
        graph = sentinel.graph

        _generate_cell_subgraph(worksheet, graph, (1, 11), set(), [])

        self.assertEqual(
            mock_add_location_dependencies.call_args,
            ((graph, (1, 11), set([(99, 98)])), {}),
        )


    @patch('sheet.dependency_graph._add_location_dependencies')
    def test_should_remove_dependencies_with_errors_and_empty_cells(
        self, mock_add_location_dependencies
    ):
        worksheet = Worksheet()
        worksheet[1, 1].formula = '1'
        worksheet[1, 2].error = CycleError([])
        worksheet[1, 3].error = SyntaxError('')
        worksheet[1, 11].formula = '=foo'
        worksheet[1, 11].dependencies = [(1, 1), (1, 2), (1, 3), (1, 4)]
        graph = sentinel.graph

        _generate_cell_subgraph(worksheet, graph, (1, 11), set(), [])

        self.assertCalledOnce(mock_add_location_dependencies,
                              graph, (1, 11), set())


    @patch('sheet.dependency_graph._generate_cell_subgraph', die(CycleError([])))
    @patch('sheet.dependency_graph._add_location_dependencies')
    @patch('sheet.dependency_graph.report_cell_error')
    def test_should_report_cell_error_and_not_add_location_on_recursive_call_raising_cycle_error_if_location_is_not_in_cycle_path(
        self, mock_report_cell_error, mock_add_location_dependencies
    ):
        worksheet = Worksheet()
        worksheet[1, 11].formula = '=A12'
        worksheet[1, 11].dependencies = [(1, 12)]

        _generate_cell_subgraph(worksheet, sentinel.graph, (1, 11), set(), [])

        self.assertCalledOnce(mock_add_location_dependencies, sentinel.graph, (1, 11), set())
        self.assertCalledOnce(mock_report_cell_error, worksheet, (1, 11), CycleError([]))


    @patch('sheet.dependency_graph._add_location_dependencies')
    def test_should_add_cell_to_graph_if_formula_not_set_but_python_formula_is(
        self, mock_add_location_dependencies
    ):
        worksheet = Worksheet()
        worksheet[1, 2].python_formula = 'blerk'

        _generate_cell_subgraph(worksheet, sentinel.graph, (1, 2), set(), [])

        self.assertCalledOnce(mock_add_location_dependencies, sentinel.graph, (1, 2), set())


    @patch('sheet.dependency_graph._add_location_dependencies')
    def test_should_not_reprocess_locations_already_in_visited_even_if_it_is_in_worksheet(
        self, mock_add_location_dependencies
    ):
        cell = Cell()
        cell.formula = 'constant'
        worksheet = Worksheet()
        worksheet[1, 2] = cell

        _generate_cell_subgraph(worksheet, sentinel.graph, (1, 2), set([(1, 2)]), [])

        self.assertFalse(mock_add_location_dependencies.called)


    @patch('sheet.dependency_graph._generate_cell_subgraph')
    @patch('sheet.dependency_graph._add_location_dependencies', Mock())
    def test_should_add_location_to_visited_set_after_recursing_deps(
        self, mock_generate_cell_subgraph
    ):
        visited = set()
        visited_set_at_time_of_recursive_call = []
        # NB: Clone visited or changes will be reflected in the one we store
        mock_generate_cell_subgraph.side_effect = lambda *_: visited_set_at_time_of_recursive_call.append(set(visited))

        worksheet = Worksheet()
        worksheet[1, 2].formula = '=23'
        worksheet[1, 2].dependencies = [(3, 4)]

        _generate_cell_subgraph(worksheet, sentinel.graph, (1, 2), visited, [])

        self.assertEquals(visited_set_at_time_of_recursive_call[0], set())
        self.assertEquals(visited, set([(1, 2)]))
        self.assertTrue(mock_generate_cell_subgraph.called)


    def test_should_safely_handle_nonexistent_location(self):
        empty_worksheet = {}
        _generate_cell_subgraph(empty_worksheet, sentinel.graph, (1, 2), set(), [])


    @patch('sheet.dependency_graph.report_cell_error')
    def test_should_report_then_raise_cycle_error_when_there_is_a_cycle(
        self, mock_report_cell_error
    ):
        cycle_error = CycleError([(1, 2), (3, 4), (1, 2)])
        worksheet = Worksheet()
        worksheet[1, 2].formula = "=foo"

        visited = set()
        try:
            _generate_cell_subgraph(worksheet, sentinel.graph, (1, 2), visited, [(8, 9), (1, 2), (3, 4)])
        except Exception, e:
            self.assertEquals(e, cycle_error)
        else:
            self.fail("No Exception raised")

        self.assertCalledOnce(mock_report_cell_error, worksheet, (1, 2), cycle_error)
        self.assertEquals(visited, set([(1, 2)]))


    def test_should_raise_any_existing_cycle_error_for_visited_locations(self):
        cycle_error = CycleError([(1, 2), (3, 4), (1, 2)])
        worksheet = Worksheet()
        worksheet[1, 2].error = cycle_error

        try:
            _generate_cell_subgraph(worksheet, sentinel.graph, (1, 2), set([(1, 2)]), sentinel.path)
        except Exception, e:
            self.assertEquals(e, cycle_error)
        else:
            self.fail("No Exception raised")


    @patch('sheet.dependency_graph._generate_cell_subgraph')
    @patch('sheet.dependency_graph.report_cell_error')
    @patch('sheet.dependency_graph._add_location_dependencies', Mock())
    def test_should_reraise_cycle_error_after_reporting_if_its_in_the_cycle_path(
        self, mock_report_cell_error, mock_recursive_call
    ):
        cycle_error = CycleError([(1, 2), (3, 4), (1, 2)])
        worksheet = Worksheet()
        worksheet[1, 2].formula = "=C4"
        mock_recursive_call.side_effect = die(cycle_error)

        visited = set()
        try:
            _generate_cell_subgraph(worksheet, sentinel.graph, (1, 2), visited, [])
        except Exception, e:
            self.assertEquals(e, cycle_error)
        else:
            self.fail("No Exception raised")

        self.assertCalledOnce(mock_report_cell_error, worksheet, (1, 2), cycle_error)
        self.assertEquals(visited, set([(1, 2)]))


    @patch('sheet.dependency_graph._generate_cell_subgraph')
    @patch('sheet.dependency_graph.report_cell_error')
    @patch('sheet.dependency_graph._add_location_dependencies', Mock())
    def test_should_not_reraise_cycle_error_if_its_outside_the_cycle_path(
        self, mock_report_cell_error, mock_recursive_call
    ):
        cycle_error = CycleError([(1, 2), (3, 4), (1, 2)])
        worksheet = Worksheet()
        worksheet[1, 3].formula = "=foo"
        mock_recursive_call.side_effect = die(cycle_error)

        _generate_cell_subgraph(worksheet, sentinel.graph, (1, 3), set(), []) # should not raise


    @patch('sheet.dependency_graph._generate_cell_subgraph')
    def test_should_not_recurse_into_existing_cycle_errors_or_include_them_in_its_deps(
        self, mock_recursive_call
    ):
        cycle_error = CycleError([(1, 2), (3, 4), (1, 2)])
        worksheet = Worksheet()
        worksheet[1, 2].error = cycle_error
        worksheet[3, 4].error = cycle_error
        worksheet[1, 3].formula = "=foo"
        worksheet[1, 3].dependencies = [(3, 4)]

        visited = set([(1, 2), (3, 4)])
        graph = {}
        _generate_cell_subgraph(worksheet, graph, (1, 3), visited, [])

        dep_cell_calls = [c[0][2] for c in mock_recursive_call.call_args_list]
        self.assertNotIn(dep_cell_calls, (3, 4))
        self.assertEquals(visited, set([(1, 2), (1, 3), (3, 4)]))
        self.assertEquals(graph, {(1, 3): Node((1, 3), set())})


    def test_does_not_include_discovered_cycle_in_deps_of_current_cell(self):#
        worksheet = Worksheet()
        worksheet[1, 1].formula = '=A2'
        worksheet[1, 2].formula = '=A1'
        worksheet[1, 3].formula = '=A1'

        visited = set()
        graph = {}

        _generate_cell_subgraph(worksheet, graph, (1, 3), visited, [])
        self.assertEquals(graph, {(1, 3): Node((1, 3), set())})
        self.assertEquals(visited, set([(1, 2), (1, 3), (1, 1)]))


    @patch('sheet.dependency_graph.report_cell_error')
    def test_reports_error_once_per_cell(self, mock_report_cell_error):
        mock_report_cell_error.side_effect = report_cell_error
        worksheet = Worksheet()
        worksheet[1, 1].formula = '=A2'
        worksheet[1, 2].formula = '=A1'

        try:
            _generate_cell_subgraph(worksheet, {}, (1, 1), set(), [])
        except CycleError:
            pass

        self.assertEquals(len(mock_report_cell_error.call_args_list), 2)


class TestDependencyGraphNode(ResolverTestCase):

    def test_constructor(self):
        self.assertRaises(TypeError, lambda: Node())

        n1 = Node((1, 2))
        self.assertEquals(n1.location, (1, 2))
        self.assertEquals(n1.children, set())
        self.assertEquals(n1.parents, set())

        n2 = Node((2, 3), children=set([1, 2, 3]))
        self.assertEquals(n2.location, (2, 3))
        self.assertEquals(n2.children, set([1, 2, 3]))
        self.assertEquals(n2.parents, set())

        n3 = Node((4, 5), parents=set([1, 2, 3]))
        self.assertEquals(n3.location, (4, 5))
        self.assertEquals(n3.children, set())
        self.assertEquals(n3.parents, set([1, 2, 3]))

    def test_nodes_should_have_a_lock(self):
        node = Node((1, 2))
        self.assertIsNotNone(node.lock.acquire)
        self.assertIsNotNone(node.lock.release)

    def test_equality(self):
        n1 = Node((1, 2), children=set([1]))
        n1.parents = set([2])
        n2 = Node((1, 2), children=set([1]))
        n2.parents = set([2])

        self.assertTrue(n1 == n2)
        self.assertFalse(n1 != n2)

        n2.location = (3, 4)
        self.assertFalse(n1 == n2)
        self.assertTrue(n1 != n2)

        n2.location = (1, 2)
        n2.parents = set([3])
        self.assertFalse(n1 == n2)
        self.assertTrue(n1 != n2)

        n2.children = set([3])
        self.assertFalse(n1 == n2)
        self.assertTrue(n1 != n2)

        n2.parents = set([2])
        self.assertFalse(n1 == n2)
        self.assertTrue(n1 != n2)

    def test_repr(self):
        self.assertEquals(
            str(Node((1, 2), children=set([1, 2, 3]))),
            "<Node 1,2 children={1, 2, 3} parents={}>"
        )

    def test_remove_should_acquire_lock_on_parent_nodes(self):
        parent1 = Node((1, 2))
        parent2 = Node((2, 3))
        node = Node((3, 4), parents=set([(1, 2), (2, 3)]))
        parent1.children = set([(3, 4)])
        parent2.children = set([(3, 4)])
        leaf_queue = Mock()

        parent1.lock = Mock()
        parent1.lock.aquire.side_effect = lambda: self.assertTrue(node in parent1.children)
        parent1.lock.release.side_effect = lambda: self.assertFalse(node in parent1.children)

        parent2.lock = Mock()
        parent2.lock.aquire.side_effect = lambda: self.assertTrue(node in parent2.children)
        parent2.lock.release.side_effect = lambda: self.assertFalse(node in parent2.children)

        node.remove_from_parents([parent1, parent2], leaf_queue)

        self.assertTrue(parent1.lock.acquire.called)
        self.assertTrue(parent1.lock.release.called)
        self.assertTrue(parent2.lock.acquire.called)
        self.assertTrue(parent2.lock.release.called)

        self.assertEquals(
            leaf_queue.put.call_args_list,
            [call((1, 2)), call((2, 3))]
        )


    def test_remove_should_add_new_leaves_to_queue(self):
        parent = Node((1, 2))
        child1 = Node((2, 3), parents=set([parent.location]))
        child2 = Node((3, 4), parents=set([parent.location]))
        parent.children = set([child1.location, child2.location])
        leaf_queue = Mock()

        child1.remove_from_parents([parent], leaf_queue)

        self.assertFalse(leaf_queue.put.called)

        child2.remove_from_parents([parent], leaf_queue)

        self.assertEquals(leaf_queue.put.call_args, ((parent.location,), {}))


class TestAddLocationDependencies(ResolverTestCase):

    def test_add_location_dependencies_does(self):
        graph = {}
        dependencies = set([sentinel.dependencies])
        _add_location_dependencies(graph, sentinel.location, dependencies)
        self.assertEquals(type(graph[sentinel.location]), Node)
        self.assertEquals(graph[sentinel.location].children, dependencies)

    def test_add_location_dependencies_also_adds_reverse_dependencies(self):
        graph = {}
        parent_loc = (1, 2)
        child1_loc = (2, 3)
        child2_loc = (3, 4)
        grandchild_loc = (4, 5)

        _add_location_dependencies(graph, parent_loc, set([child1_loc, child2_loc]))
        expected = {
            parent_loc: Node(parent_loc, children=set([child1_loc, child2_loc])),
            child1_loc: Node(child1_loc, parents=set([parent_loc])),
            child2_loc: Node(child2_loc, parents=set([parent_loc])),
        }
        self.assertEquals(expected, graph)

        _add_location_dependencies(graph, grandchild_loc, set())
        expected = {
            parent_loc: Node(parent_loc, children=set([child1_loc, child2_loc])),
            child1_loc: Node(child1_loc, parents=set([parent_loc])),
            child2_loc: Node(child2_loc, parents=set([parent_loc])),
            grandchild_loc: Node(grandchild_loc),
        }
        self.assertEquals(expected, graph)

        _add_location_dependencies(graph, child1_loc, set([grandchild_loc]))
        expected = {
            parent_loc: Node(parent_loc, children=set([child1_loc, child2_loc])),
            child1_loc: Node(
                child1_loc,
                children=set([grandchild_loc]),
                parents=set([parent_loc])
            ),
            child2_loc: Node(child2_loc, parents=set([parent_loc])),
            grandchild_loc: Node(grandchild_loc, parents=set([child1_loc])),
        }
        self.assertEquals(expected, graph)

