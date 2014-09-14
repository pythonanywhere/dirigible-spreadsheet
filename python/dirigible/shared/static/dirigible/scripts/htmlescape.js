// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

function htmlescape(untrusted_string) {
    var better_string = untrusted_string.replace(/&/g, '&amp;');
    better_string = better_string.replace(/>/g, '&gt;');
    better_string = better_string.replace(/</g, '&lt;');
    better_string = better_string.replace(/"/g, '&quot;');
    better_string = better_string.replace(/'/g, '&#39;');
    return better_string;
}
