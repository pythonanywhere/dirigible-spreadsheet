// Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
// See LICENSE.md
//


editor_methods = {

    init: function(args) {
        this.$input = $("<input type='text' class='editor-text' />")
            .bind("keydown.nav", function(e) {
                if (e.keyCode === $.ui.keyCode.LEFT || e.keyCode === $.ui.keyCode.RIGHT) {
                    e.stopImmediatePropagation();
                }
            })
            .appendTo(args.container);
        if (document.activeElement !== args.formula_bar[0] ) {
            this.$input.focus();
        }
        this.column = args.column;
        this.$formula_bar = args.formula_bar;

        var that = this;
        var updating = false;

        this.updateFormulaBarIfChanged = function(new_value) {
            if (that.$formula_bar.val() !== new_value) {
                that.$formula_bar.val(new_value);
            }
        };
        this._updateFormulaBar = function() {
            if (updating) {
                return;
            }
            updating = true;
            that.updateFormulaBarIfChanged(that.$input.val());
            updating = false;
        };
        this.$input.bind("input", this._updateFormulaBar);
        this.$input.bind("propertychange", this._updateFormulaBar);

        this.updateInput = function() {
            if (updating) {
                return;
            }
            updating = true;
            that.$input.val(that.$formula_bar.val());
            updating = false;
        };
        this.$formula_bar.bind("input", this.updateInput);
        this.$formula_bar.bind("propertychange", this.updateInput);

        this.forwardReturnsToEditor = function(evt) {
            if (evt.which == 13) {
                var refirableEvent = $.Event("keydown");
                refirableEvent.which = 13;
                that.$input.trigger(refirableEvent);
            }
        };
        this.$formula_bar.bind("keydown", this.forwardReturnsToEditor);
    },

    destroy: function () {
        this.$input.remove();
        this.$formula_bar.unbind("input", this.updateInput);
        this.$formula_bar.unbind("propertychange", this.updateInput);
        this.$formula_bar.unbind("keydown", this.forwardReturnsToEditor);
    },

    loadValue: function (gridRow) {
        var newValue = "";
        if (gridRow !== undefined && gridRow[this.column.field] !== undefined) {
            newValue = gridRow[this.column.field].formula || "";
        }
        this.defaultValue = newValue;
        this.setInputElementValues(newValue);
        this.$input[0].defaultValue = newValue;
    },

    setInputElementValues: function(value) {
        this.$input.val(value);
        this.$input.caret(value.length, value.length);
        this.updateFormulaBarIfChanged(value);
    },

    serializeValue: function () {
        return {formula: this.$input.val()};
    },

    applyValue: function (item, state) {
        item[this.column.field] = state;
    },

    isValueChanged: function () {
        return (
            !(this.$input.val() === "" && this.defaultValue === null) &&
            this.$input.val() !== this.defaultValue
        );
    },

    validate: function () {
        return {
            valid: true,
            msg: null
        };
    }
};


function CellEditorFactory(currying_formula_bar) {
    return function(args) {
        $.extend(this, editor_methods);
        this.init($.extend({ formula_bar : currying_formula_bar }, args));
    };
}
