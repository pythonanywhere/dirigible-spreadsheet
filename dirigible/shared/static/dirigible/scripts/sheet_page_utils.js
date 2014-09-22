(function($) {
    // register namespace
    $.extend(true, window, {
        "Dirigible": {
            "SheetUtils": {
                "Initialise": InitialiseSheetUtils
            }
        }
    });


    function InitialiseSheetUtils(urls, pageView) {
        var _self = this;

        function createNewGrid() {
        }


        function queueRecalculation() {
            $.ajaxq('recalculation_queue', {
                type: 'get',
                url: urls.calculate,
                success: getMetaData
            });
        }


        function abortOtherRecalculations() {
            $.ajaxq('recalculation_queue');
        }


        function getMetaData(content) {
            if (content === 'OK') {
                $.ajaxq('get_json_queue');
                $.ajaxq('get_json_queue', {
                    type: 'get',
                    dataType: 'json',
                    url: urls.getJSONMetaData,
                    success: pageView.updateMetaData
                });
            }
        }


        $.extend(true, window, {
            "Dirigible": {
                "SheetUtils": {
                    "createNewGrid": createNewGrid,
                    "queueRecalculation": queueRecalculation,
                    "getMetaData": getMetaData,
                    "abortOtherRecalculations": abortOtherRecalculations
                }
            }
        });

    }

})(jQuery);

