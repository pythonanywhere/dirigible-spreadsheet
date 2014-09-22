// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//


function elementVisible(element, expected, message) {
    if (message == undefined) {
        message = '';
    } else {
        message = ': ' + message
    }
    YAHOO.util.Assert.isTrue(element.length > 0, 'element(s) should exist' + message);
    actual = element.is(':visible');
    var ids = '';
    element.each(function () {ids += this.id;});
    YAHOO.util.Assert.areSame(expected, actual, 'wrong visibility for ' + ids + message);
}


function assertDeepAreSame(expected, actual, message) {
    if (message == undefined) {
        message = "<root object>";
    } else {
        message = message + "  Path: <root object>";
    }

    var finalMessage = _deepAreSame(expected, actual, message);
    if (finalMessage){
        throw new YAHOO.util.ComparisonFailure(finalMessage, expected, actual);
    }

}


function _deepAreSame(expected, actual, message) {
    if (typeof(expected) !== typeof(actual)) {
        if (actual === undefined) {
            return message + " property missing from actual";
        }
        return (
            message + ' types differ ' +
            '(expected is ' + typeof(expected) +
            ', actual is ' + typeof(actual) + ')'
        );
    }

    switch (typeof(expected)) {
        case 'object':
            for (p in expected) {
                var recurseDown = _deepAreSame(
                        expected[p], actual[p], message + '.' + p
                );
                if (recurseDown) {
                    return recurseDown;
                }
            }
            break;

        case 'function':
            if (typeof(actual) == 'undefined'
                ||
                (expected.toString() != actual.toString())
            ) {
                return (
                    message + " methods exist on both " +
                    "expected and actual but differ\n" +
                    "expected : " + expected.toString() + "\n" +
                    "actual : " + actual.toString()
                );
            }
            break;

        default:
            if (expected !== actual){
                return (
                    message + ' property differs, ' +
                    expected + ' !== ' + actual
                );
            }
            break;
    }

    for (p in actual) {
        if (
                typeof(actual[p]) != 'undefined' &&
                typeof(expected[p]) == 'undefined'
        ) {
            return message + "." + p + " property unexpectedly on actual";
        }
    }
}


