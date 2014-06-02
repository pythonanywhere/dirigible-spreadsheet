// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//


(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "PageCommands": PageCommands
        }
    });

    function PageCommands(gridCommands, editorCommands) {
        var self = this;

        self.recalculate = function() {
            editorCommands.saveUsercode();
            gridCommands.commitCurrentEdit();
            Dirigible.SheetUtils.abortOtherRecalculations();
            Dirigible.SheetUtils.queueRecalculation();
        }
    }

})(jQuery);

