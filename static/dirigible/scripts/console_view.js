// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "ConsoleView": ConsoleView
        }
    });

    function ConsoleView($consoleDiv) {
        var self = this;

        self.updateMetaData = function(sheetMetaData) {
            if ('console_text' in sheetMetaData) {
                $consoleDiv.html(sheetMetaData['console_text']);
            } else {
                $consoleDiv.html('');
            }
        };
    }

})(jQuery);
