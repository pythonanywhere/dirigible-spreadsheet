// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "GridView": GridView
        }
    });

    var editor_locator = 'input.editor-text';
    var formula_bar_locator = '#id_formula_bar';

    function GridView(grid, remoteModel) {
        var self = this;
        self.grid = grid;
        self.remoteModel = remoteModel;

        self.with_restore_cursor = function( wrapped_function ) {
            var f = function() {
                var current_selected_editor_locator = null;
                var caret = null;
                if (document.activeElement == $(editor_locator)[0]) {
                    current_selected_editor_locator = editor_locator;
                    caret = $(current_selected_editor_locator).caret();
                } else if (document.activeElement == $(formula_bar_locator)[0]) {
                    current_selected_editor_locator = formula_bar_locator;
                    caret = $(current_selected_editor_locator).caret();
                }
                var contents = $(editor_locator).val();

                wrapped_function.apply(null, arguments);

                if (current_selected_editor_locator !== null) {
                    self.grid.editActiveCell();
                }

                $(editor_locator).val(contents);
                $(formula_bar_locator).val(contents);

                if (current_selected_editor_locator !== null) {
                    $(current_selected_editor_locator).focus();
                    $(current_selected_editor_locator).caret(
                        caret.start, caret.end
                    );
                }
            };

            f.wrapped = true; // for testing
            return f
        };

        self.updateMetaData = self.with_restore_cursor(
            function(sheetMetaData) {
                var rows = Dirigible.GridView.jsonToSlickGridRowHeaders(sheetMetaData);
                self.remoteModel.reset(rows);
                self.grid.render();
                self.ensureCurrentViewportData();
            }
        );

        self.ensureCurrentViewportData = function() {
            var $viewport = $('div.slick-viewport');
            var topLeft = grid.getCellFromPoint(
                $viewport.scrollLeft(), $viewport.scrollTop()
            );
            var bottomRight = grid.getCellFromPoint(
                $viewport.scrollLeft() + $viewport.width(),
                $viewport.scrollTop() + $viewport.height()
            );
            self.remoteModel.ensureData(
                topLeft.cell, topLeft.row,
                bottomRight.cell, bottomRight.row
            );
        };

        self.handleOnDataLoading = function() {
            $('#id_buffering_message').removeClass('hidden');
        };
        self.remoteModel.onDataLoading.subscribe(self.handleOnDataLoading);

        self.handleOnDataLoaded = self.with_restore_cursor(
            function(event, loadedRange) {
                for (var row=loadedRange.topmost; row <= loadedRange.bottom; row++) {
                    grid.invalidateRow(row - 1);
                }

                grid.updateRowCount();
                grid.render();
                $('#id_buffering_message').addClass('hidden');
            }
        );

        self.remoteModel.onDataLoaded.subscribe(self.handleOnDataLoaded);

        self.grid.onScroll.subscribe(self.ensureCurrentViewportData);

    };


    GridView.jsonToSlickGridData = function(jsonData) {
        var slickgrid_sheet = [];
        for (i=0; i < jsonData.height; i++) {
            slickgrid_sheet[i] = jQuery.extend(
                { header: i + 1 }, jsonData[i + 1]
            );
        }
        return slickgrid_sheet;
    };

    GridView.jsonToSlickGridRowHeaders = function(jsonData) {
        var height = jsonData.height || 1000;
        var slickgrid_sheet = [];
        for (var ii = 1; ii <= height; ii++) {
            slickgrid_sheet.push({header: ii});
        }
        return slickgrid_sheet;
    }

    GridView.jsonToSlickGridColumnHeaders = function(jsonData) {
        var width = jsonData.width || 52;
        var sheet_columns = [{
            name: "",
            field: "header",
            id: "header",
            width: 40,
            sortable: false,
            unselectable: true
        }];
        for (var ii = 1; ii <= width; ii++) {
            var column_name = GridView.columnIndexToName(ii);
            var fieldID = "" + ii;
            var column_options = {
                name: column_name,
                field: fieldID,
                id: fieldID,
                formatter: GridView.cellFormatter};
            if (jsonData.column_widths && jsonData.column_widths[ii]) {
                column_options.width = jsonData.column_widths[ii];
            }
            sheet_columns.push(column_options);
        }
        return sheet_columns;
    };

    GridView.columnIndexToName = function(index) {
        var columnName = '';
        while (index > 0) {
            var thisChar = String.fromCharCode((index - 1) % 26 + 65);
            index = Math.floor((index - 1) / 26);
            columnName = thisChar + columnName;
        }
        return columnName;
    };


    GridView.cellFormatter = function(row, column, cell, columnDef, dataContext) {
        if (cell !== undefined && cell.error !== undefined) {
            row = row + 1;
            return "<img id='id_" + column + "_" + row + "_error' " +
                        "title='" + htmlescape(cell.error) + "' " +
                        "src='/static/dirigible/images/error.gif' />";
        }
        if (cell === undefined) {
            return "";
        }
        if (cell.formatted_value === undefined) {
            if (cell.formula) {
                var escaped_formula = htmlescape(cell.formula);
                return (
                    '<span class="grid_formula" title="'+ escaped_formula +'">' +
                    escaped_formula + "</span>"
                );
            } else {
                return "";
            }
        }
        var escaped_formatted_value = htmlescape(cell.formatted_value);
        return (
            '<span class="grid_formatted_value" title="'+ escaped_formatted_value +'">' +
            escaped_formatted_value + "</span>"
        );
    };


})(jQuery);
