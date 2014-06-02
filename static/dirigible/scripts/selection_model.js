// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

(function($) {
    // register namespace
    $.extend(true, window, {
        Dirigible: {
            SelectionModel: SelectionModel
        }
    });



    function SelectionModel() {
        this.selectors = [
            new Slick.CellRangeSelector(),
            new Dirigible.KeyboardCellRangeSelector()
        ];
        this.onSelectedRangesChanged = new Slick.Event();
        this.ranges = [];
    }


    SelectionModel.prototype.init = function(grid) {
        this.grid = grid;
        this.handleActiveCellChanged = this.getHandleActiveCellChanged();
        this.grid.onActiveCellChanged.subscribe(this.handleActiveCellChanged);

        this.handleBeforeCellRangeSelected = this.getHandleBeforeCellRangeSelected();
        this.handleCellRangeSelected = this.getHandleCellRangeSelected();
        for (var i=0; i < this.selectors.length; i++) {
            var selector = this.selectors[i];
            this.grid.registerPlugin(selector);
            selector.onBeforeCellRangeSelected.subscribe(this.handleBeforeCellRangeSelected);
            selector.onCellRangeSelected.subscribe(this.handleCellRangeSelected);
        }
    };


    SelectionModel.prototype.destroy = function() {
        this.grid.onActiveCellChanged.unsubscribe(this.handleActiveCellChanged);
        for (var i=0; i < this.selectors.length; i++) {
            var selector = this.selectors[i];
            selector.onBeforeCellRangeSelected.unsubscribe(this.handleBeforeCellRangeSelected);
            selector.onCellRangeSelected.unsubscribe(this.handleCellRangeSelected);
            this.grid.unregisterPlugin(selector);
        }
    };


    SelectionModel.prototype.getSelectedRanges = function() {
        return this.ranges;
    };


    SelectionModel.prototype.setSelectedRanges = function(ranges) {
        this.ranges = ranges;
        this.onSelectedRangesChanged.notify(this.ranges);
    };


    SelectionModel.prototype.getHandleActiveCellChanged = function() {
        var _self = this;
        return function(event, cell) {
            var activeCell = _self.grid.getActiveCell();
            _self.setSelectedRanges([new Slick.Range(
                    activeCell.row, activeCell.cell,
                    activeCell.row, activeCell.cell)]);
        };
    };


    SelectionModel.prototype.getHandleBeforeCellRangeSelected = function() {
        var _self = this;
        return function(event, cell) {
            if (_self.grid.canCellBeSelected(cell.row, cell.cell)) {
                _self.grid.getEditController().commitCurrentEdit();
                _self.grid.setActiveCell(cell.row, cell.cell);
            }
            return true;
        };
    };


    SelectionModel.prototype.getHandleCellRangeSelected = function() {
        var _self = this;
        return function(event, args) {
            _self.setSelectedRanges([args.range]);
        };
    };


})(jQuery);
