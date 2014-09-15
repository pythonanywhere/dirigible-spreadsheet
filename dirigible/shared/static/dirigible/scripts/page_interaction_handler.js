// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//
(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "PageInteractionHandler": PageInteractionHandler
        }
    });

    function PageInteractionHandler(
        $, pageView, pageCommands, editor, editorCommands, grid, gridCommands
    ) {
        var self = this;
        self.commitCurrentEdit = function() {
            gridCommands.commitCurrentEdit();
        };

        self.initialiseComponents = function(urls, editable) {
            if (editable) {
                $('#id_sheet_name').eip(
                    urls.setSheetName,
                    {
                        select_text : true,
                        form_buttons : '',
                        text_form: '<input type="text" id="edit-#{id}" class="#{editfield_class}" value="#{value}" /> ',
                        after_save: pageView.updatePageTitle
                    }
                );
            }

            $("#id_grid_and_code").splitter({
                splitVertical: true,
                outline: true,
                anchorToWindow: true,
                sizeLeft: true,
                cookie: 'dirigible_vertical_splitter'
            });
            $("#id_right_column").splitter({
                splitHorizontal: true,
                outline: true,
                anchorToWindow: true,
                sizeBottom: true,
                cookie: 'dirigible_horizontal_splitter'
            });
        };

        self.resizeComponents = function(event) {
            $('#id_console').width($('#id_right_column').width() - 20);
            $('#id_console').height($('#id_console_wrap').height() - 20);

            var gridAndFormulaBarHeight = $('#id_left_column').height() - 10;
            $('#id_grid_and_formula_bar').height(gridAndFormulaBarHeight);
            $('#id_grid').height(gridAndFormulaBarHeight - $('#id_formula_bar').height() - 18);
            $('#id_formula_bar').width($('#id_grid').width() - 8);
            grid.resizeCanvas();

            if ($('#id_usercode_wrap').height() < 30) {
                $('#id_usercode').hide();
            } else {
                $('#id_usercode').show();
            }
            $('#id_usercode').width($('#id_usercode_wrap').width() - 20);
            $('#id_usercode').height($('#id_usercode_wrap').height() - 10);
            editor.resize();
        };


        self.bind = function() {
            // Click-away handlers
            editor.addEventListener('click', self.commitCurrentEdit);
            $('#id_right_column, #id_header_and_toolbar').bind(
                'click', self.commitCurrentEdit
            );

            editor.addEventListener('blur', editorCommands.saveUsercode);
            editor.usercodeDirty = false;
            editor.getSession().addEventListener(
                'change', function() {
                    editor.usercodeDirty = true;
                });

            // Ctrl-S always saves usercode.
            // and F9 recalculates
            $(document).keydown(
                function(event) {
                    if (event.ctrlKey && event.which === 83) {
                        editorCommands.saveUsercode();
                        event.preventDefault();
                    } else if (event.which === 120) {
                        pageCommands.recalculate();
                        event.preventDefault();
                    }
                }
            );

            $(document).mouseup(function() {
                window.setTimeout(self.resizeComponents, 0);
            });
            $(window).resize(function(event) {
                window.setTimeout(self.resizeComponents, 0);
            });
        };

    }

})(jQuery);
