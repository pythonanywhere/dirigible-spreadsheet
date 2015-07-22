# How does a spreadsheet work?

    @hjwp

    www.pythonanywhere.com
    www.obeythetestinggoat.com



# this talk

https://github.com/pythonanywhere/dirigible-spreadsheet

"slides": in repo, documentation/talk.md






good colourschemes:  nightsky, pspad, sea





























# Data structure

```python
worksheet = {}
worksheet[row_no, col_no] = cell_object
```
































# The most basic calculation... how?

= 1 + 1
--> should give 2
* the formula/value distinction


```python
class Cell:
    def __init__(self):
        self.formula = ''
        self.value = undefined


def calculate(worksheet):
    for cell in worksheet.values():
        if cell.formula.startswith('=')
            cell.value = ???
        else:
            cell.value = cell.formula
```
















# The most basic calculation - answered

= 1 + 1
--> should give 2
* the formula/value distinction


```python
class Cell:
    def __init__(self):
        self.formula = ''
        self.value = undefined


def calculate(worksheet):
    for cell in worksheet.values():
        if cell.formula.startswith('=')
            cell.value = eval(cell.formula)
        else:
            cell.value = cell.formula
```





















# Exceptions:

```python
    try:
        cell.value = eval(cell.formula)
    except Exception as e:
        cell.value = undefined
        cell.error = str(e)
    # ...
```

































# References

= A1 + A2
We want to change this so that A1 and A2 become references to worksheet cells:
= worksheet[1, 1].value + worksheet[1, 2].value
ie excel formula -> python formula


```python
def calculate(worksheet):
        #...
            cell.value = eval(cell._python_formula)
        #...


class Cell:
    def __init__(self):
        self.value = undefined
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

    formula = property(_get_forumla, _set_formula)
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
``





























`

And it looks like this:

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

find and load constants first...

```python

def calculate_cell(cell):
    try:
        cell.value = eval(cell._python_forumla)
    #...



def load_constants(worksheet):
    for loc, cell in worksheet.items():
        if not cell._python_formula:
            cell.value = cell._formula
```
































Now we build a graph and calculate them, starting from "leaves"


```python
def calculate(worksheet):
    load_constants(worksheet)

    leaves = build_dependency_graph(worksheet)

    while leaves:
        leaf = leaves.pop()
        cell = worksheet[leaf.location]

        calculate_cell(cell)
        
        remove_from_parents(node, leaves) 


def remove_from_parents(node, leaves):
    for parent in node.parents:
        parent.children.remove(node)
        if not parent.children:
            leaves.append(parent)
```

(and you can parallelise this stuff too)
































# Building the dependency graph

two-way graph...

```python
def build_dependency_graph(worksheet):
    graph = {}
    completed = set()
    for location in worksheet.keys():
        _generate_cell_subgraph(worksheet, graph, location, completed)


def _generate_cell_subgraph(worksheet, graph, location, completed):
    if location in completed:
        return

    cell = worksheet[location]
    _add_location_dependencies(graph, location, cell.dependencies)

    for dependency_location in cell.dependencies:
        _generate_cell_subgraph(
            worksheet, graph, dependency_location, completed 
        )

    completed.add(location)


def _add_location_dependencies(graph, location, dependencies):
    if location not in graph:
        graph[location] = Node(location)

    graph[location].children.add(dependencies)

    for dependency in dependencies:
        if dependency not in graph:
            graph[dependency] = Node(dependency)
        graph[dependency].parents.add(location)
```
































## Detecting cycles



```python
def build_dependency_graph(worksheet):
    graph = {}
    completed = set()
    for location in worksheet.keys():
        _generate_cell_subgraph(worksheet, graph, location, completed, path=[])

def _generate_cell_subgraph(worksheet, graph, location, completed, path):
    if location in completed:
        return

    if location in path:
        raise CycleError(path[path.index(location):] + [location])

    cell = worksheet[location]
    for dependency_location in cell.dependencies:
        try:
            _generate_cell_subgraph(
                worksheet, graph, dependency_location, completed, path + [location]
            )

        except CycleError as cycle_error:
            cell.error = cycle_error
            if location in cycle_error.path:
                completed.add(location)
                raise cycle_error

    _add_location_dependencies(graph, location, cell.dependencies)
    completed.add(location)






























```


# Custom functions

    def foo(x):
        return x + 2


time to isolate our evals from the global context a little...

```python

def calculate(worksheet, usercode):
    context = {}
    context['worksheet'] = worksheet

    eval(usercode, context)

    #.... loop thru graph
        cell.value = eval(cell.python_formula, context)
```
































# OK, but what if we want to access to some spreadsheet values?


* introducing `load_constants` and `evaluate_formulae`:

```python

def calculate(worksheet, usercode):
    load_constants(worksheet)

    context = {}
    context['worksheet'] = worksheet

    load_constants(worksheet, context)

    eval(usercode, context)

    evaluate_formulae(worksheet, context)


def load_constants(worksheet):
    for cell in worksheet.values():
        if not cell.startswith('='):
            cell.value = cell.formula

def evaluate_formulae(worksheet, context):
    leaves = build_dependency_graph(worksheet)
    while leaves:
        #...
        calculate_cell(cell)
```
































# OK, but what if the user wants access formula results?



```python

def calculate(worksheet, usercode_pre_formula_eval, usercode_post_formula_eval):
    load_constants(worksheet)

    context = {}
    context['worksheet'] = worksheet

    load_constants(worksheet, context)

    eval(usercode_pre_formula_eval, context)

    evaluate_formulae(worksheet, context)

    eval(usercode_post_formula_eval, context)
```
































# notice we can now programatically generate formulae...

```python

worksheet[1, 3].formula = "=A1+ A2"
```

First mwahahaha moment.

But wait, there's more!
































# And now, time for some real fun

Reminder of what we're doing at the moment...

```python

def calculate(worksheet, usercode_pre_formula_eval, usercode_post_formula_eval):
    load_constants(worksheet)

    context = {}
    context['worksheet'] = worksheet

    load_constants(worksheet, context)

    eval(usercode_pre_formula_eval, context)

    evaluate_formulae(worksheet, context)

    eval(usercode_post_formula_eval, context)
```


This is what the user sees:


```python
load_constants(worksheet)

# Put code here if it needs to access constants in the spreadsheet
# and to be accessed by the formulae.  Examples: imports,
# user-defined functions and classes you want to use in cells.

evaluate_formulae(worksheet)

# Put code here if it needs to access the results of the formulae.
```






























the usercode *is* the spreadsheet!

```python

def load_constants(worksheet):
    #...

def evaluate_formulae(worksheet, context):
    #...

def calculate(worksheet, usercode, private_key):
    evaluate_formulae_in_context = lambda worksheet: \
        evaluate_formulae(worksheet, context)
    context = {
        'worksheet': worksheet,
        'load_constants': load_constants,
        'evaluate_formulae': evaluate_formulae_in_context,
        'undefined': undefined,
    }
    try:
        exec(usercode, context)
    except Exception as e:
        add_to_console(e)
```




so an example, a retirement calculator

