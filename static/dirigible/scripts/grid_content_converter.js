// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

function getGridCellFormula(grid, slickCellLocation) {
    var columnField = grid.getColumns()[slickCellLocation.cell].field;
    var rowData = grid.getDataItem(slickCellLocation.row);
    if (rowData !== undefined) {
        var cellData = rowData[columnField];
        if (cellData !== undefined && cellData.formula !== undefined) {
            return cellData.formula;
        }
    }
    return "";
}


function slickGridCellDataToPostParams(grid, slickCellLocation) {
    return {
        column: slickCellLocation.cell,
        row: slickCellLocation.row + 1,
        formula: grid.getCellFormula(slickCellLocation)
    };
}
