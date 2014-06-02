# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from dirigible.sheet.formula_interpreter import (
        get_dependencies_from_parse_tree,
        get_python_formula_from_parse_tree
)
from dirigible.sheet.parser import FormulaError, parser



class Undefined(object):

    def __repr__(self):
        return "<undefined>"


undefined = Undefined()


class Cell(object):

    def __init__(self):
        self.clear()


    def _set_formula(self, value):
        self._python_formula = None
        if value is None:
            self._formula = None
        elif type(value) == str or type(value) == unicode:
            self._formula = value
            if value.startswith('='):
                try:
                    parsed_formula = parser.parse(value)
                    self.dependencies = get_dependencies_from_parse_tree(parsed_formula)
                    self._python_formula = get_python_formula_from_parse_tree(parsed_formula)
                except FormulaError, e:
                    self.dependencies = []
                    self._python_formula = '_raise(FormulaError("%s"))' % (e,)
        else:
            raise TypeError('cell formula must be str or unicode')

    def _get_formula(self):
        return self._formula

    formula = property(_get_formula, _set_formula)


    def _set_python_formula(self, value):
        if type(value) == str or type(value) == unicode:
            self._python_formula = value
        else:
            raise TypeError('cell python_formula must be str or unicode')

    def _get_python_formula(self):
        return self._python_formula

    python_formula = property(_get_python_formula, _set_python_formula)


    def _set_value(self, value):
        self._value = value
        if value is undefined:
            self._set_formatted_value(u'')
        else:
            self._set_formatted_value(unicode(value))

    def _get_value(self):
        return self._value

    value = property(_get_value, _set_value)

    def clear_value(self):
        self._value = undefined


    def _set_formatted_value(self, value):
        if value is None:
            self._formatted_value = u''
        elif type(value) == str or type(value) == unicode:
            self._formatted_value = value
        else:
            raise TypeError('cell formatted_value must be str or unicode')

    def _get_formatted_value(self):
        return self._formatted_value

    formatted_value = property(_get_formatted_value, _set_formatted_value)


    def clear(self):
        self._value = undefined
        self._formula = None
        self._python_formula = None
        self.dependencies = []
        self._formatted_value = u''
        self.error = None


    def __repr__(self):
        error = ""
        if self.error:
            error = " error=%r" % (self.error,)
        return '<Cell formula=%s value=%r formatted_value=%r%s>' % \
            (self.formula, self._value, self.formatted_value, error)


    def __eq__(self, other):
        return (
            isinstance(other, Cell) and
            self._formula == other.formula and
            self._value == other.value and
            self._formatted_value == other.formatted_value and
            self.error == other.error
        )


    def __ne__(self, other):
        return not self.__eq__(other)
