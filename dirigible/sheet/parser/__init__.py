class FormulaError(Exception):
    """
    This exception is used to indicate that a cell expression is badly formed.
    It is the equivalent of a ``SyntaxError`` in normal Python code.
    """