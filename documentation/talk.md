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
class Cell(object):
    def __init__(self):
        self.formula = ''
        self.value = ''
        self.error = None


def calculate(worksheet):
    for cell in worksheet.values():
        cell.value = eval(cell.formula)
```

# exceptions:

```python
    for cell in worksheet:
        try:
            cell.value = eval(cell.formula)
        except Exception as e:
            cell.value = UNDEFINED
            cell.error = str(e)
```


# References

= A1 + A2

We want to change this so that A1 and A2 become references to worksheet cells:

= worksheet[1, 1].value + worksheet[1, 2].value


```python
def calculate(worksheet):

    for cell in worksheet.values():
        try:
            cell.value = eval(cell._python_formula)
        #...


class Cell(object):
    def __init__(self):
        self.value = ''
        self._formula = ''
        self._python_formula = ''
        self.error = None

    def _set_formula(self, user_input):
        self._python_formula = None
        if user_input.startswith('='):
            self._formula = user_input
            try:
                parsed_formula = parser.parse(user_input)
                self._python_formula = get_python_formula_from_parse_tree(
                    parsed_formula
                )

            except FormulaError as e:
                self._python_formula = '_raise(FormulaError("{}"))'.format(e)

    def _get_formula(self):
        return self._formula
```

```python
def get_python_formula_from_parse_tree(parse_node):
    return rewrite(parse_node).flatten()[1:]

def rewrite(parse_node):
    if isinstance(parse_node, ParseNode):
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

Tests, if you're curious:

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
def calculate(worksheet):
    graph, leaves = build_dependency_graph(worksheet)
    while leaves:
        leaf = leaves.pop()
        cell = worksheet[leaf.location]
        try:
            cell.value = eval(cell.python_formula)
        #...

        for parent in leaf.parents:
            parent.dependencies.remove(cell)
            if not parent.dependencies:
                leaves.append(parent)
```

(and you can parallelise this stuff too)


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

