
function escape_quotes(key, value) {
    if (typeof value === 'string') {
        // just replacing '<' seems enough to cause json encoding to
        // kick in for '>', etc.
        return value.replace(/\</g, '&lt;');
    }
    return value;
}

YAHOO.util.Event.onDOMReady(function () {
    var testRunner = YAHOO.tool.TestRunner;
    for (var i in tests) {
        testRunner.add(tests[i]);
    }
    testRunner.subscribe(
        testRunner.COMPLETE_EVENT,
        function(data) {
            JSON.useNativeStringify = false;
            document.getElementById("id_results").innerHTML = JSON.stringify(data.results, escape_quotes);
        }
    );
    var oLogger = new YAHOO.tool.TestLogger();
    testRunner.run();
});

