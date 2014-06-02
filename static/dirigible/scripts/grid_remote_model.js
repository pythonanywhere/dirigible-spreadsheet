(function($) {
    $.extend(true, window, {
        "Dirigible": {
            "GridRemoteModel": GridRemoteModel
        }
    });

	function GridRemoteModel(urls) {
        var self = this;

        self.data = [];
        self.url = urls.getJSONGridData;
        self.patches = {};
        self.pending = {};
        self.patchWidth = 26;
        self.patchHeight = 100;
        
        self.getLength = function() {
            return self.data.length;
        };
        
        self.getItem = function(index) {
            return self.data[index];
        };

        self.cellToPatch = function(col, row) {
            return {
                patchCol: Math.floor( Math.max((col - 1), 0) / self.patchWidth ),
                patchRow: Math.floor( Math.max((row - 1), 0) / self.patchHeight )
            };
        };

        self.patchToCells = function(patch) {
            return {
                left: patch.patchCol * self.patchWidth + 1,
                topmost: patch.patchRow * self.patchHeight + 1,
                right: patch.patchCol * self.patchWidth + self.patchWidth,
                bottom: patch.patchRow * self.patchHeight + self.patchHeight
            };
        };

		self.choosePatchesToLoad = function(left, topmost, right, bottom) {
            var patchesToLoad = [];
            var nw = self.cellToPatch(left, topmost);
            var se = self.cellToPatch(right, bottom);
            for (var patchCol = nw.patchCol; patchCol <= se.patchCol; patchCol++) {
                for (var patchRow = nw.patchRow; patchRow <= se.patchRow; patchRow++) {
                    patchesToLoad.push( { patchCol: patchCol, patchRow: patchRow } );
                }
            }
            return patchesToLoad;
        };


        self.isPatchLoadedOrPending = function(patch) {
            if (self.patches[patch.patchCol] !== undefined) {
                if(self.patches[patch.patchCol][patch.patchRow] !== undefined){
                    return true;
                }
            }
            if (self.pending[patch.patchCol] !== undefined) {
                if(self.pending[patch.patchCol][patch.patchRow] !== undefined){
                    return true;
                }
            }
            return false;
        };


        self.loadPatchIfNecessary = function(patch) {
            if (!self.isPatchLoadedOrPending(patch)) {
                var range = self.patchToCells(patch);
                if (self.pending[patch.patchCol] === undefined){
                    self.pending[patch.patchCol] = {};
                }
                self.pending[patch.patchCol][patch.patchRow] = true;
                self.onDataLoading.notify();
                self.getData(range.left, range.topmost, range.right, range.bottom, patch);
            }
        };


        self.getData = function (left, topmost, right, bottom, patch) {
            var range = left + ', ' + topmost + ', ' + right + ', ' + bottom;
            $.getJSON(self.url, {'range' : range}, self.getSuccessHandlerForPatch(patch) );
        };


		self.ensureData = function(left, topmost, right, bottom) {
            var patchesToLoad = self.choosePatchesToLoad(left, topmost, right, bottom);
            for (var patch=0; patch<patchesToLoad.length; patch++) {
                self.loadPatchIfNecessary(patchesToLoad[patch]);
            }
		};


		self.onDataLoading = new Slick.Event();
		self.onDataLoaded = new Slick.Event();


		self.onError = function(fromPage,toPage) {
			console.log("error loading pages " + fromPage + " to " + toPage);
		};


        self.addData = function(jsonData) {
            for (var row=jsonData.topmost; row <= jsonData.bottom; row++ ) {
                if (self.data[row - 1] === undefined) {
                    self.data[row - 1] = { header: row };
                }
                for (
                    var column=jsonData.left;
                    column <= jsonData.right;
                    column++)
                {
                    if (
                        jsonData[row] !== undefined &&
                        jsonData[row][column] !== undefined)
                    {
                        self.data[row - 1][column] = jsonData[row][column];
                    } else {
                        delete self.data[row - 1][column];
                    }
                }
            }
        };

        self.getSuccessHandlerForPatch = function(patch) {
            return function(jsonData) {
                self.onSuccess(jsonData);

                var expectedArea = self.patchToCells(patch);
                if (jsonData.left > expectedArea.left 
                    || jsonData.topmost > expectedArea.topmost 
                    || jsonData.right < expectedArea.right 
                    || jsonData.bottom < expectedArea.bottom){
                    return
                }
                if (self.patches[patch.patchCol] === undefined){
                    self.patches[patch.patchCol] = {};
                }
                self.patches[patch.patchCol][patch.patchRow] = true;
                if (self.pending[patch.patchCol] !== undefined) {
                    delete self.pending[patch.patchCol][patch.patchRow];
                }
            };
        };

		self.onSuccess = function(jsonData) {
            self.addData(jsonData);
			self.onDataLoaded.notify({
                    left: jsonData.left,
                    topmost: jsonData.topmost,
                    right: jsonData.right,
                    bottom: jsonData.bottom
            });
		};

        self.reset = function(newData) {
            self.data = newData;
            self.patches = {};
            self.pending = {};
        };
    }
})(jQuery);
