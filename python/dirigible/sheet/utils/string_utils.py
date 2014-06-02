# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

def get_rstripped_part(string):
    strippedString = string.rstrip()
    whitespace = string[len(strippedString):]
    return whitespace


def get_lstripped_part(string):
    strippedString = string.lstrip()
    whitespace = string[:-len(strippedString)]
    return whitespace


def double_quote_repr_string(inString):
    result = repr(inString)[1:-1]
    result = result.replace('"', '\\"')
    result = result.replace("\\'", "'")
    return "\"%s\"" % result


def correct_case(candidate, potentialMatches):
    for match in potentialMatches:
        if match.lower() == candidate.lower():
            return match
    return candidate
