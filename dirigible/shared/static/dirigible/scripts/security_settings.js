// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//

(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "SecuritySettings": {
                "Dialog" : Dialog,
                "Model" : Model
            }
        }
    });


    function Model($, urls) {
        var self = this;


        self.updatePageUI = function() {
            var securityButton = $('#id_security_button');
            var title_text = 'Sheet security settings (';
            if (self.isPublic) {
                title_text += 'Sheet is public. ';
            } else {
                title_text += 'Sheet is private. ';
            }
            if (self.enabled) {
                title_text += 'JSON API enabled)';
            } else {
                title_text += 'JSON API disabled)';
            }
            securityButton.attr('alt', title_text);
            securityButton.attr('title', title_text);
        };

        self.updateServerState = function(
            publicSheetCheckboxState,
            jsonAPICheckboxState,
            jsonAPIKeyFieldValue,
            successHandler,
            errorHandler
        ) {
            $.ajax({
                type: "POST",
                url: urls.setSecuritySettings,
                data: {
                    'is_public': publicSheetCheckboxState,
                    'allow_json_api_access': jsonAPICheckboxState,
                    'api_key': jsonAPIKeyFieldValue
                },
                success: function(data) {
                    self.handleServerUpdateResponse(
                        data,
                        publicSheetCheckboxState,
                        jsonAPICheckboxState,
                        jsonAPIKeyFieldValue,
                        successHandler,
                        errorHandler
                    );
                },
                error: errorHandler
            });
        };

        self.handleServerUpdateResponse = function(data,
            publicSheetCheckboxState, jsonAPICheckboxState,
            jsonAPIKeyFieldValue, successHandler, errorHandler)
        {
            if (data === 'OK') {
                successHandler();
                self.isPublic = publicSheetCheckboxState;
                self.enabled = jsonAPICheckboxState;
                self.apiKey = jsonAPIKeyFieldValue;
                self.updatePageUI();
            } else {
                errorHandler();
            }
        };

    }


    function Dialog($, urls) {
        var self = this;

        self.show = function(model) {
            self.model__ = model;
            $('#id_security_form_save_error').addClass('hidden');
            self.updateDialogUI(model.isPublic, model.enabled, model.apiKey);
            $('#id_security_form').dialog({ width: 400 });
        };

        self.updateDialogUI = function(isPublic, enabled, apiKey) {
            $('#id_security_form_json_enabled_checkbox').attr('checked', enabled);
            $('#id_security_form_public_sheet_checkbox').attr('checked', isPublic);
            $apiKeyField = $('#id_security_form_json_api_key');
            $apiUrlField = $('#id_security_form_json_api_url');
            self.enableJsonApiFields_(enabled);
            $apiKeyField.val(apiKey);
            self.updateAPIURL();
        };

        self.enableJsonApiFields_ = function(enabled) {
            if (enabled){
                $apiKeyField.attr('disabled', '');
                $apiUrlField.attr('disabled', '');
            } else {
                $apiKeyField.attr('disabled', 'disabled');
                $apiUrlField.attr('disabled', 'disabled');
            }
        };

        self.updateAPIURL = function() {
            var newApiUrl = 'http://' + window.location.host
                + urls.apiBase + '?api_key=' +
                $('#id_security_form_json_api_key').val();
            $('#id_security_form_json_api_url').val(newApiUrl);
        };

        self.updateDialogUIFromCheckboxes = function() {
            var checkboxJSON = $('#id_security_form_json_enabled_checkbox');
            var stateJSON = checkboxJSON.attr('checked');
            var checkboxPublic = $('#id_security_form_public_sheet_checkbox');
            var statePublic = checkboxPublic.attr('checked');
            self.enableJsonApiFields_(stateJSON);
        };

        self.onOK = function() {
            var publicCheckboxState = $('#id_security_form_public_sheet_checkbox').attr('checked');
            var jsonAPICheckboxState = $('#id_security_form_json_enabled_checkbox').attr('checked');
            var jsonAPIKeyFieldValue = $('#id_security_form_json_api_key').val();
            self.model__.updateServerState(
                publicCheckboxState,
                jsonAPICheckboxState,
                jsonAPIKeyFieldValue,
                self.close,
                self.handleSaveError
            );
            return false;
        };

        self.close = function() {
            $('#id_security_form').dialog("close");
        };

        self.handleSaveError = function() {
            $('#id_security_form_save_error').removeClass('hidden');
        };

        self.selectFullURL_ = function() {
            $(this).caret(0, $(this).val().length);
        };

        self.bind = function(model) {

            $('#id_security_form_ok_button').click(self.onOK);
            $('#id_security_form_cancel_button').click(self.close);

            $('#id_security_form_json_api_key').bind(
                'keyup mouseup change select',
                self.updateAPIURL
            );

            $('#id_security_form_json_enabled_checkbox').click(self.updateDialogUIFromCheckboxes);

            $('#id_security_form_json_api_url').click(self.selectFullURL_);
            $('#id_security_form_json_api_key').click(self.selectFullURL_);
        };

    }

})(jQuery);
