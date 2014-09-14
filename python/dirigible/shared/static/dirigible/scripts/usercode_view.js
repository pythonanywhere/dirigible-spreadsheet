// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "UsercodeView": UsercodeView
        }
    });

    function UsercodeView(editor) {
        var self = this;

        self.initialiseComponents = function(editable) {
            var PythonMode = require("ace/mode/python").Mode;
            editor.getSession().setMode(new PythonMode());
            editor.setReadOnly(!editable);
        };

        self.updateMetaData = function(sheetMetaData) {
            var annotations = [];
            if ('usercode_error' in sheetMetaData) {
                annotations.push( {
                    row: parseInt(sheetMetaData.usercode_error.line) - 1,
                    column: 0,
                    text: sheetMetaData.usercode_error.message,
                    type: "error"
                } );
            }
            editor.getSession().setAnnotations(annotations);
        };

    }

})(jQuery);
