(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "Dialogs": {
                "Initialise": Initialise
            }
        }
    });

function Initialise(grid, urls) {
    var _self = this;
    _self.grid = grid;

    $('#id_import_form_file').change(function() {
        if($('#id_import_form_file').val().match(/\.xls$/)) {
            $('#id_import_form_upload_xls_values_button').show();
            $('#id_import_form_upload_csv_button').hide();
            $('#id_import_form span.import_form_radio_button').hide();
            $('#id_import_form form').attr('action', urls.importXls);
        } else {
            $('#id_import_form span.import_form_radio_button').show();
            $('#id_import_form_upload_csv_button').show();
            $('#id_import_form_upload_xls_values_button').hide();
            $('#id_import_form form').attr('action', urls.importCsv);
        }
    });

    $('#id_import_form_cancel_button').click( function() {
        $('#id_import_form').dialog("close");
    });
    $('#id_export_dialog_close_button').click( function() {
        $('#id_export_dialog').dialog("close");
    });

    $('#id_import_button').click(importButtonClickHandler);
    $('#id_export_button').click(function() {$('#id_export_dialog').dialog({width: 450});});

    function importButtonClickHandler() {
        $('#id_import_form form')[0].reset();
        var column = 1;
        var row = 1;
        var gridActiveCell = _self.grid.getActiveCell();
        if (gridActiveCell) {
            column = gridActiveCell.cell;
            row = gridActiveCell.row + 1;
            $('#id_import_form_column').val(column);
            $('#id_import_form_row').val(row);
        }
        $('#id_import_form_upload_csv_button').hide();
        $('#id_import_form span.import_form_radio_button').hide();
        $('#id_import_form_upload_xls_values_button').hide();
        $('#id_import_form').dialog();
    }
}

})(jQuery);
