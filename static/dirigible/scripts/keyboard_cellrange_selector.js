// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

var TAB = 9;
var SHIFT = 16;


(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "KeyboardCellRangeSelector": KeyboardCellRangeSelector
        }
    });

    function KeyboardCellRangeSelector() {
        this.isShiftDown = false;
        this.startCell = null;
    }

    KeyboardCellRangeSelector.prototype.init = function (grid) {
        this.grid = grid;
        grid.onKeyDown.subscribe(this.getKeyDownHandler());
        grid.onActiveCellChanged.subscribe(this.getActiveCellChangedHandler());
        $(window.document).keyup(this.getKeyUpHandler());
    };

    KeyboardCellRangeSelector.prototype.destroy = function () {
    };

    KeyboardCellRangeSelector.prototype.getKeyDownHandler = function () {
        var _self = this;
        return function (event) {
            if (event.which === SHIFT) {
                _self.isShiftDown = true;
                _self.startCell = _self.grid.getActiveCell();
            }
            else if (event.which === TAB)
            {
                _self.isShiftDown = false;
                _self.startCell = null;
            }
        };
    };
    KeyboardCellRangeSelector.prototype.getKeyUpHandler = function () {
        var _self = this;
        return function (event) {
            if (event.which === SHIFT) {
                _self.isShiftDown = false;
                _self.startCell = null;
            }
        };
    };

    KeyboardCellRangeSelector.prototype.getActiveCellChangedHandler = function () {
        var _self = this;
        return function (event, cell) {
            if (_self.startCell && _self.isShiftDown) {
                var new_range = new Slick.Range(
                        _self.startCell.row, _self.startCell.cell,
                        cell.row, cell.cell
                );
                _self.onCellRangeSelected.notify({range: new_range});
            }
        };
    };

    KeyboardCellRangeSelector.prototype.onBeforeCellRangeSelected = new Slick.Event();

    KeyboardCellRangeSelector.prototype.onCellRangeSelected = new Slick.Event();



})(jQuery);

