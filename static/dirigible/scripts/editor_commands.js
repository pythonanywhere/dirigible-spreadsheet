// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//


(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "EditorCommands": EditorCommands
        }
    });

    function EditorCommands(urls, editor) {

        function saveUsercode() {
            if (!editor.usercodeDirty) {
                return;
            }
            Dirigible.SheetUtils.abortOtherRecalculations();
            var text = editor.getSession().getValue();
            $.post(
                urls.setSheetUsercode,
                { usercode: text },
                Dirigible.SheetUtils.queueRecalculation
            );
            editor.usercodeDirty = false;
        }

        $.extend(
            this,
            {
                'saveUsercode': saveUsercode
            }
        );
    }

})(jQuery);

