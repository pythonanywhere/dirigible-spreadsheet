// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//


(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "GridCommands": GridCommands
        }
    });


    function GridCommands(urls, grid) {
        var self = this;
        self.urls = urls;

        self.getPostFunction__ = function (name, recalculate) {
            var callback = undefined;
            if (recalculate) {
                callback = Dirigible.SheetUtils.queueRecalculation;
            }

            return function (startCol, startRow, endCol, endRow) {
                $.post(
                    self.urls[name],
                    {range: startCol+','+startRow+','+endCol+','+endRow},
                    callback
                );
            };
        };


        self.sendCopyToServer__ = self.getPostFunction__('copy', false);
        self.sendCutToServer__ = self.getPostFunction__('cut', true);
        self.sendPasteToServer__ =self.getPostFunction__('paste', true);
        self.sendClearToServer__ = self.getPostFunction__('clearCells', true);

        self.copy = Dirigible.GridCommands.createSelectionCommand__(
                    grid, self.sendCopyToServer__);
        self.cut = Dirigible.GridCommands.createSelectionCommand__(
                    grid, self.sendCutToServer__);
        self.paste = Dirigible.GridCommands.createSelectionCommand__(
                    grid, self.sendPasteToServer__);
        self.clear = Dirigible.GridCommands.createSelectionCommand__(
                    grid, self.sendClearToServer__);


        self.resizeColumns = function(gridColumns) {
            var columnWidths = self.convertGridColumnsToJSON__(grid.getColumns());
            $.post(urls.setColumnWidths, {column_widths: columnWidths});
        };


        self.convertGridColumnsToJSON__ = function(gridColumns) {
            var columnWidths = {};
            for (var i=0; i < gridColumns.length; i++) {
                var col = gridColumns[i];
                if (col.previousWidth != col.width) {
                    columnWidths[String(i)] = col.width;
                }
            }
            return JSON.stringify(columnWidths);
        };


        self.sendCellChangeToServer = function(event, gridLocation, retries) {
            Dirigible.SheetUtils.abortOtherRecalculations();
            retries = (retries === undefined) ? 5 : retries;
            $.post(
                urls.setCellFormula,
                slickGridCellDataToPostParams(grid, gridLocation),
                function(response) {
                    if (response === 'FAILED' && retries > 0) {
                        self.sendCellChangeToServer(
                            event, gridLocation, retries - 1
                        );
                    } else {
                        self.setCellFormulaAndUpdateSheet__(gridLocation);
                    }
                }
            );
        };


        self.setCellFormulaAndUpdateSheet__ = function (gridLocation) {
            grid.updateCell(gridLocation.row, gridLocation.column);
            Dirigible.SheetUtils.queueRecalculation();
        };

        self.commitCurrentEdit = function () {
            grid.getEditController().commitCurrentEdit();
        }

    }

    Dirigible.GridCommands.createSelectionCommand__ = function(grid, command) {
        return function() {
            if (grid.getCellEditor() === null) {
                var selectedRange = (
                    grid.getSelectionModel().getSelectedRanges()[0]
                );
                command(
                    selectedRange.fromCell,
                    selectedRange.fromRow + 1,
                    selectedRange.toCell,
                    selectedRange.toRow + 1
                );
                return true;
            }
            return false;
        };
    };

})(jQuery);

