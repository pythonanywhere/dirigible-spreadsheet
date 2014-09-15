(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "FeedbackDialog": {
                "Initialise": Initialise
            }
        }
    });

function Initialise(urls, username) {
    var _self = this;

    var default_email = "Email address (optional - only necessary if you would like us to contact you)";
    if (username !== '') {
        $('#id_feedback_dialog_email_address').hide();
    } else {
        $('#id_feedback_dialog_email_address').val(default_email);
        $('#id_feedback_dialog_email_address').addClass('email_prompt');
        $('#id_feedback_dialog_email_address').focus(function() {
            $('#id_feedback_dialog_email_address').removeClass('email_prompt');
            if ($('#id_feedback_dialog_email_address').val() == default_email) {
                $('#id_feedback_dialog_email_address').val('');
            }
        });
    }

    $('.feedback_link').click(function(event) {
        $('#id_feedback_dialog_error').addClass('hidden');
        $('#id_feedback_dialog_spinner').addClass('hidden');
        $('#id_feedback_dialog_ok_button').removeAttr('disabled');
        $('#id_feedback_dialog_cancel_button').removeAttr('disabled');
        $('#id_feedback_dialog').dialog({
                width: 600
        });
        event.preventDefault();
    });

    $('#id_feedback_dialog_ok_button').click(function() {
        $('#id_feedback_dialog_spinner').removeClass('hidden');
        $('#id_feedback_dialog_ok_button').attr('disabled', 'disabled');
        $('#id_feedback_dialog_cancel_button').attr('disabled', 'disabled');
        $('#id_feedback_dialog_error').addClass('hidden');
        $.ajax({
            type:'POST',
            url: urls.feedback,
            data: {
                message: $('#id_feedback_dialog_text').val(),
                email_address: $('#id_feedback_dialog_email_address').val(),
                username: username
            },
            error: function() {
                $('#id_feedback_dialog_error').removeClass('hidden');
                $('#id_feedback_dialog_ok_button').removeAttr('disabled');
                $('#id_feedback_dialog_cancel_button').removeAttr('disabled');
                $('#id_feedback_dialog_spinner').addClass('hidden');
            },
            success: function() {
                $('#id_feedback_dialog').dialog("close");
            }
        });
    });

    $('#id_feedback_dialog_cancel_button').click(function() {
        $('#id_feedback_dialog_error').addClass('hidden');
        $('#id_feedback_dialog').dialog("close");
    });

}

})(jQuery);
