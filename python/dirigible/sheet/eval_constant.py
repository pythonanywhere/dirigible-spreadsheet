# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#


def eval_constant(constant):
    try:
        temp = float(constant)
        try:
            return int(constant)
        except ValueError:
            return temp
    except ValueError:
        return constant

