(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "GridInteractionHandler": GridInteractionHandler
        }
    });

    function GridInteractionHandler($, grid, gridCommands, gridRemoteModel) {
        var self = this;
        self.handleKeyDown = function(event) {
            var TAB       = 9;
            var DEL       = 46;
            var BACKSPACE = 8;
            var LEFT      = 37;
            var UP        = 38;
            var PAGE_DOWN = 34;
            var PAGE_UP   = 33;
            var HOME      = 36;
            var END       = 35;
            var LETTER_C  = 67;
            var LETTER_V  = 86;
            var LETTER_X  = 88;
            var F2        = 113;

            if (event.ctrlKey || event.metaKey) {
                switch (event.which) {
                    case LETTER_X:
                        if (gridCommands.cut()) {
                            event.stopImmediatePropagation();
                        }
                        break;
                    case LETTER_C:
                        if (gridCommands.copy()) {
                            event.stopImmediatePropagation();
                        }
                        break;
                    case LETTER_V:
                        if (gridCommands.paste()) {
                            event.stopImmediatePropagation();
                        }
                        break;
                    case HOME:
                        grid.gotoCell(0, 1);
                        event.stopImmediatePropagation();
                        break;
                    case END:
                        grid.gotoCell(grid.getDataLength() - 1, grid.getColumns().length - 1);
                        event.stopImmediatePropagation();
                        break;
                }
            } else {
                switch (event.which) {
                    case BACKSPACE:
                    case DEL:
                        if (gridCommands.clear()) {
                            event.stopImmediatePropagation();
                        }
                        break;
                    case LEFT:
                        if (grid.getActiveCell().cell === 1) {
                            event.stopImmediatePropagation();
                        }
                        break;

                    case UP:
                        if (grid.getActiveCell().row === 0) {
                            event.stopImmediatePropagation();
                        }
                        break;

                    case PAGE_DOWN:
                        var viewport = grid.getViewport();
                        var newTopRow = viewport.bottom - 1;
                        var activeCell = grid.getActiveCell();
                        var pageSize = viewport.bottom - viewport.top - 1;
                        if (viewport.bottom < grid.getDataLength()) {
                            grid.scrollRowIntoView(newTopRow, true);
                        }
                        grid.gotoCell(activeCell.row + pageSize, activeCell.cell);
                        event.stopImmediatePropagation();
                        break;

                    case PAGE_UP:
                        var viewport = grid.getViewport();
                        var activeCell = grid.getActiveCell();
                        var pageSize = viewport.bottom - viewport.top - 1;
                        var newTopRow = viewport.top - pageSize;
                        if (newTopRow < 0) {
                            newTopRow = 0;
                        }
                        grid.scrollRowIntoView(newTopRow, false);
                        grid.gotoCell(activeCell.row - pageSize, activeCell.cell);
                        event.stopImmediatePropagation();
                        break;

                    case F2:
                        grid.editActiveCell();
                        break;
                }
            }
        };

        self.handleGridDivKeyPress = function(event) {
            if (event.ctrlKey || event.altKey) {
                return true;
            }
            if (event.which > 47 || event.which === 32) {
                if (grid.getCellEditor() === null ) {
                    grid.editActiveCell();
                    grid.getCellEditor().setInputElementValues(String.fromCharCode(event.which));
                    return false;
                }
            }
            return true;
        };

        self.updateFormulaBar = function() {
            var activeCell = grid.getActiveCell();
            if (!activeCell) {
                return;
            }
            $('#id_formula_bar').val(grid.getCellFormula(activeCell));
        };

        self.handleFormulaBarClick = function () {
            if (grid.getCellEditor() === null) {
                grid.editActiveCell();
            }
            var $formulaBar = $('#id_formula_bar');
            var caret = $formulaBar.caret();
            $formulaBar.focus();
            $formulaBar.caret(caret.start, caret.end);
            
        };

        self.bind = function() {
            grid.onKeyDown.subscribe(self.handleKeyDown);

            $('#id_grid').keypress(self.handleGridDivKeyPress);
            $('#id_formula_bar').click(self.handleFormulaBarClick);

            grid.onColumnsResized.subscribe(gridCommands.resizeColumns);
            grid.onCellChange.subscribe(gridCommands.sendCellChangeToServer);
            grid.onActiveCellChanged.subscribe(self.updateFormulaBar);
            grid.onClick.subscribe(self.updateFormulaBar);
        };
    }

})(jQuery);

