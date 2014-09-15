(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "ToolbarInteractionHandler": ToolbarInteractionHandler
        }
    });

    function ToolbarInteractionHandler(gridCommands, pageCommands) {
        var self = this;
        self.bind = function() {
            $('#id_cut_button').click(gridCommands.cut);
            $('#id_copy_button').click(gridCommands.copy);
            $('#id_paste_button').click(gridCommands.paste);
            $('#id_recalc_button').click(pageCommands.recalculate);
        };
    }

})(jQuery);

