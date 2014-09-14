# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from threading import Lock

from .errors import report_cell_error, CycleError


class Node(object):
    def __init__(self, location, children=None, parents=None):
        self.location = location
        self.children = children if children else set()
        self.parents = parents if parents else set()
        self.lock = Lock()

    def __eq__(self, other):
        return (
            self.location == other.location and
            self.children == other.children and
            self.parents == other.parents
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<Node %d,%d children={%s} parents={%s}>" % (
            self.location[0], self.location[1],
            ', '.join(str(i) for i in self.children),
            ', '.join(str(i) for i in self.parents))

    def remove_from_parents(self, parent_nodes, leaf_queue):
        for parent in parent_nodes:
            parent.lock.acquire()
            parent.children.remove(self.location)
            if len(parent.children) == 0:
                leaf_queue.put(parent.location)
            parent.lock.release()




def build_dependency_graph(worksheet):
    graph = {}
    visited = set()
    for loc in worksheet.keys():
        try:
            _generate_cell_subgraph(worksheet, graph, loc, visited, [])
        except CycleError:
            pass # Deal with escapees

    leaves = []
    for loc, deps in graph.iteritems():
        if not deps.children:
            leaves.append(loc)

    return graph, leaves


def _generate_cell_subgraph(worksheet, graph, loc, completed, path):
    if loc not in worksheet:
        return
    cell = worksheet[loc]
    if loc in completed:
        if type(cell.error) == CycleError:
            raise cell.error
        else:
            return

    if loc in path:
        cycle_error = CycleError(path[path.index(loc):] + [loc])
        report_cell_error(worksheet, loc, cycle_error)
        completed.add(loc)
        raise cycle_error

    if cell.python_formula:
        valid_dependencies = set()
        for dep_loc in cell.dependencies:
            dep_cell = worksheet[dep_loc]
            try:
                _generate_cell_subgraph(worksheet, graph, dep_loc, completed, path + [loc])

                if dep_cell.error:
                    continue
                if not dep_cell.python_formula:
                    continue
                valid_dependencies.add(dep_loc)
            except CycleError as cycle_error:
                if not loc in completed:
                    report_cell_error(worksheet, loc, cycle_error)
                if loc in cycle_error.path:
                    completed.add(loc)
                    raise cycle_error
        _add_location_dependencies(graph, loc, valid_dependencies)
    completed.add(loc)


def _add_location_dependencies(graph, location, dependencies):
    if location not in graph:
        graph[location] = Node(location)
    graph[location].children |= dependencies
    for dependency in dependencies:
        if dependency not in graph:
            graph[dependency] = Node(dependency)
        graph[dependency].parents.add(location)


