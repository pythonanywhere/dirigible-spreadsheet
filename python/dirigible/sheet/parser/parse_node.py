# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#


class ParseNode(object):

    AND_TEST                        = "AND_TEST"
    ARG_LIST                        = "ARG_LIST"
    ARGUMENT                        = "ARGUMENT"
    ARITH_EXPR                      = "ARITH_EXPR"
    ATOM                            = "ATOM"
    COMP_OPERATOR                   = "COMP_OPERATOR"
    COMPARISON                      = "COMPARISON"
    CONCAT_EXPR                     = "CONCAT_EXPR"
    DICT_MAKER                      = "DICT_MAKER"
    EXPR                            = "EXPR"
    EXPR_LIST                       = "EXPR_LIST"
    EXTENDED_SLICING                = "EXTENDED_SLICING"
    FACTOR                          = "FACTOR"
    FL_CELL_RANGE                   = "FL_CELL_RANGE"
    FL_CELL_REFERENCE               = "FL_CELL_REFERENCE"
    FL_COLUMN_REFERENCE             = "FL_COLUMN_REFERENCE"
    FL_ROW_REFERENCE                = "FL_ROW_REFERENCE"
    FL_DDE_CALL                     = "FL_DDE_CALL"
    FL_DELETED_REFERENCE            = "FL_DELETED_REFERENCE"
    FL_INVALID_REFERENCE            = "FL_INVALID_REFERENCE"
    FL_NAKED_WORKSHEET_REFERENCE    = "FL_NAKED_WORKSHEET_REFERENCE"
    FL_NAMED_COLUMN_REFERENCE       = "FL_NAMED_COLUMN_REFERENCE"
    FL_NAMED_ROW_REFERENCE          = "FL_NAMED_ROW_REFERENCE"
    FL_REFERENCE                    = "FL_REFERENCE"
    FL_ROOT                         = "FL_ROOT"
    FP_DEF                          = "FP_DEF"
    FP_LIST                         = "FP_LIST"
    GEN_FOR                         = "GEN_FOR"
    GEN_IF                          = "GEN_IF"
    GEN_ITER                        = "GEN_ITER"
    LAMBDEF                         = "LAMBDEF"
    LIST_FOR                        = "LIST_FOR"
    LIST_IF                         = "LIST_IF"
    LIST_ITER                       = "LIST_ITER"
    LIST_MAKER                      = "LIST_MAKER"
    NAME                            = "NAME"
    NOT_TEST                        = "NOT_TEST"
    NUMBER                          = "NUMBER"
    PERCENT                         = "PERCENT"
    POWER                           = "POWER"
    SHIFT_EXPR                      = "SHIFT_EXPR"
    SLICE_OP                        = "SLICE_OP"
    STRINGLITERAL                   = "STRINGLITERAL"
    SUBSCRIPT                       = "SUBSCRIPT"
    SUBSCRIPT_LIST                  = "SUBSCRIPT_LIST"
    SUM_ARGLIST                     = "SUM_ARGLIST"
    TERM                            = "TERM"
    TEST                            = "TEST"
    TEST_LIST                       = "TEST_LIST"
    TEST_LIST_GEXP                  = "TEST_LIST_GEXP"
    TRAILER                         = "TRAILER"
    VAR_ARGS_LIST                   = "VAR_ARGS_LIST"


    def __init__(self, _type, children):
        self.type = _type
        self.children = children


    def __repr__(self):
        if self.children:
            childrenStr = " children=%r" % (self.children)
        else:
            childrenStr = ""
        return "<%s type=\"%s\"%s>" % (self.__class__.__name__, self.type, childrenStr)

    __str__ = __repr__

    def __eq__(self, other):
        if other is None:
            return False
        if type(self) != type(other):
            return False
        if self.type != other.type:
            return False
        if hasattr(other.children, "__len__") ^ hasattr(self.children, "__len__"):
            return False
        if len(self.children) != len(other.children):
            return False
        for selfChild, otherChild in zip(self.children, other.children):
            if selfChild != otherChild:
                return False

        return True


    def __ne__(self, other):
        return not self.__eq__(other)


    def __hash__(self):
        raise TypeError("mutable objects are unhashable")


    def flatten(self):
        def AppendChild(string, child):
            if isinstance(child, ParseNode):
                return string + child.flatten()
            return string + child if child is not None else string
        return reduce(AppendChild, self.children, "")


    classRegistry = {}

    @classmethod
    def register_node_type(cls, nodeType, nodeClass):
        cls.classRegistry[nodeType] = nodeClass


    @classmethod
    def construct_node(cls, nodeType, children):
        if nodeType in cls.classRegistry:
            retVal = cls.classRegistry[nodeType](children)
            return retVal
        else:
            return cls(nodeType, children)
