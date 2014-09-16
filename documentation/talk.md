# Data structure

```python
worksheet = {}
worksheet[row_no, coll_no] = cell_object
```


# The most basic calculation:

= 1 + 1

--> should give 2


* the formula/value distinction

```python
class Cell:
    def __init__(self):
        self.formula = ''
        self.value = ''
        self.error = None


def calculate(worksheet):
    for cell in worksheet.values():
        if cell.formula.startswith('=')
            cell.value = eval(cell.formula)
        else:
            cell.value = cell.formula
```


# exceptions:

```python
    try:
        cell.value = eval(cell.formula)
    except Exception as e:
        cell.value = UNDEFINED
        cell.error = str(e)
    # ...
```



# References

= A1 + A2

We want to change this so that A1 and A2 become references to worksheet cells:

= worksheet[1, 1].value + worksheet[1, 2].value


```python
def calculate(worksheet):
        #...
            cell.value = eval(cell._python_formula)
        #...


class Cell:
    def __init__(self):
        self.value = ''
        self._formula = ''
        self._python_formula = ''
        self.error = None

    def _set_formula(self, user_input):
        self._formula = user_input
        self._python_formula = None
        if user_input.startswith('='):
            try:
                self._python_formula = get_python_formula_from_parse_tree(
                    parser.parse(user_input)
                )

            except FormulaError as e:
                self._python_formula = '_raise(FormulaError("{}"))'.format(e)

    def _get_formula(self):
        return self._formula
```


Let the recursive fun begin!

Test-first:

```python
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
```


```python
def get_python_formula_from_parse_tree(parse_node):
    return rewrite(parse_node).flatten()[1:]

def rewrite(parse_node):
    if parse_node.type == ParseNode.FL_CELL_RANGE:
        return rewrite_cell_range(parse_node)

    elif parse_node.type in CELL_REFERENCES:
        return rewrite_cell_reference(parse_node)

    elif parse_node.type in CONTAIN_COLONS:
        parse_node.children = map(
            rewrite,
            [transform_arrow(child) for child in parse_node.children]
        )

    else:
        parse_node.children = map(rewrite, parse_node.children)

    return parse_node

def rewrite_cell_reference(cell_reference_node):
    # essentially, transform "A1" into "worksheet[1, 1].value"
```


OK, but now I can't calculate A3 until I know the values of A2 and A1!



# Dependencies

```python
    def _set_formula(self, value):
        #...
        parsed_formula = parser.parse(value)
        self.dependencies = get_dependencies_from_parse_tree(parsed_formula)
        self._python_formula = get_python_formula_from_parse_tree(parsed_formula)
```

```python

def calculate_cell(cell):
    if cell._python_formula:
        try:
            cell.value = eval(cell._python_forumla)
        #...
    else:
        cell.value = cell.formula


def calculate(worksheet):
    leaves = build_dependency_graph(worksheet)
    while leaves:
        leaf = leaves.pop()
        cell = worksheet[leaf.location]

        calculate_cell(cell)

        for parent in leaf.parents:
            parent.children.remove(cell)
            if not parent.children:
                leaves.append(parent)
```

(and you can parallelise this stuff too)


# Building the dependency graph

two-way graph...

```python
def build_dependency_graph(worksheet):
    graph = {}
    visited = set()
    for loc in worksheet.keys():
        _generate_cell_subgraph(worksheet, graph, loc, visited, [])


def _generate_cell_subgraph(worksheet, graph, loc, completed, path):
    cell = worksheet[loc]
    if loc in completed:
        return

    if loc in path:
        raise CycleError(path[path.index(loc):] + [loc])

    if cell._python_formula:
        valid_dependencies = set()
        for dep_loc in cell.dependencies:
            try:
                _generate_cell_subgraph(
                    worksheet, graph, dep_loc, completed, path + [loc]
                )
                dep_cell = worksheet[dep_loc]

            except CycleError as cycle_error:
                if loc in cycle_error.path:
                    completed.add(loc)
                    raise cycle_error

        _add_location_dependencies(graph, loc, cell.dependencies)
    completed.add(loc)

def _add_location_dependencies(graph, location, dependencies):
    if location not in graph:
        graph[location] = Node(location)

    graph[location].children.add(dependencies)

    for dependency in dependencies:
        if dependency not in graph:
            graph[dependency] = Node(dependency)
        graph[dependency].parents.add(location)
```


# Custom functions

def foo(x):
    return x + 2

```python

def calculate(worksheet, usercode):
    context = {}
    context['worksheet'] = worksheet

    eval(usercode, context)

    #.... loop thru graph
        cell.value = eval(cell.python_formula, context)
```


# OK, but what if the user wants to programatically generate some formulae?

```python

def calculate(worksheet, usercode_pre_formula_eval, usercode_post_formula_eval):
    context = {}
    context['worksheet'] = worksheet

    eval(usercode_pre_formula_eval, context)

    #.... loop thru graph
        cell.value = eval(cell.python_formula, context)

    eval(usercode_post_formula_eval, context)
```

# And now, time for some real fun

the usercode *is* the spreadsheet!

