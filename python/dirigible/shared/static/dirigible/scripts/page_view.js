// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "PageView": PageView
        }
    });

    function PageView(username, consoleView, usercodeView, gridView) {
        var self = this;

        self.updateMetaData = function(sheetMetaData) {
            if (sheetMetaData === null || sheetMetaData === undefined) {
                return;
            }

            consoleView.updateMetaData(sheetMetaData);
            usercodeView.updateMetaData(sheetMetaData);
            gridView.updateMetaData(sheetMetaData);

            $('#id_sheet_name').text(sheetMetaData.name);
            self.updatePageTitle();
        };

        self.updatePageTitle = function() {
            document.title = username + "'s " +
                             $('#id_sheet_name').text() +
                             ": Dirigible";
        };

    }

})(jQuery);
