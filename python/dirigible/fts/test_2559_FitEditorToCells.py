# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest


class Test_2559_FitEditorToCells(FunctionalTest):

    def test_editor_fits_cells(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        cell_locator = self.get_cell_locator(3, 3)
        cell_width = self.selenium.get_element_width(cell_locator)
        cell_height = self.selenium.get_element_height(cell_locator)

        # * He edits a cell and notes that the editor fits the
        #   cell exactly
        self.open_cell_for_editing(3, 3)
        editor_locator = 'css=input.editor-text'
        editor_width = self.selenium.get_element_width(editor_locator)
        editor_height = self.selenium.get_element_height(editor_locator)

        self.assertTrue(cell_width - editor_width <= 6, "cell width: %d, editor width: %d" % (cell_width, editor_width))
        self.assertTrue(cell_height - editor_height <= 6, "cell height: %d, editor height: %d" % (cell_height, editor_height))
