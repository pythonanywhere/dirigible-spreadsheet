# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2795_Rewrite_Formulae_during_Cut_and_Paste(FunctionalTest):

    def test_cut_cell_reference_to_cut_cell_is_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * He writes a formula in A1 that refers to cell A2
        self.enter_cell_text(1, 1, '=A2')
        self.wait_for_spinner_to_stop()
        self.wait_for_cell_to_contain_formula(1, 1, '=A2')

        # * He uses cut & paste to move the formula (and its depenency)
        #   from A1 to C2
        self.cut_range((1, 1), (1, 2))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is sensibly rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=C3')


    def test_cut_cell_reference_to_uncut_cell_is_not_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * He writes a formula in A1 that refers to cell B3
        self.enter_cell_text(1, 1, '=B3')
        self.wait_for_spinner_to_stop()
        self.wait_for_cell_to_contain_formula(1, 1, '=B3')

        # * He uses cut & paste to move the formula from A1 to C2
        self.cut_range((1, 1), (1, 1))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula remains unchanged
        self.wait_for_cell_to_contain_formula(3, 2, '=B3')


    def test_copied_cell_reference_to_copied_cell_is_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * He writes a formula in A1 that refers to cell A2
        self.enter_cell_text(1, 1, '=A2')
        self.wait_for_spinner_to_stop()
        self.wait_for_cell_to_contain_formula(1, 1, '=A2')

        # * He uses copy & paste to move the formula (and its depenency)
        #   from A1 to C2
        self.copy_range((1, 1), (1, 2))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is sensibly rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=C3')


    def test_copied_cell_reference_to_uncopied_cell_is_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * He writes a formula in A1 that refers to cell B3
        self.enter_cell_text(1, 1, '=B3')
        self.wait_for_spinner_to_stop()
        self.wait_for_cell_to_contain_formula(1, 1, '=B3')

        # * He uses copy & paste to move the formula from A1 to C2
        self.copy_range((1, 1), (1, 1))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is sensibly rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=D4')


    def test_cut_cellrange_reference_to_completely_cut_cellrange_is_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing A2:A3
        self.enter_cell_text(1, 1, '=A2:A3')
        self.wait_for_cell_to_contain_formula(1, 1, '=A2:A3')

        # * He uses cut & paste to move the formula, but not its dependencies,
        #   2 along and 1 down
        self.cut_range((1, 1), (1, 3))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is sensibly rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=C3:C4')


    def test_cut_cellrange_reference_to_partially_cut_cellrange_is_not_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing A2:A3
        self.enter_cell_text(1, 1, '=A2:A3')
        self.wait_for_cell_to_contain_formula(1, 1, '=A2:A3')

        # * He uses cut & paste to move the formula, but not its dependencies,
        #   2 along and 1 down
        self.cut_range((1, 1), (1, 2))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is not rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=A2:A3')


    def test_cut_cellrange_reference_to_uncut_cellrange_is_not_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing A2:A3
        self.enter_cell_text(1, 1, '=A2:A3')
        self.wait_for_cell_to_contain_formula(1, 1, '=A2:A3')

        # * He uses cut & paste to move the formula, but not its dependencies,
        #   2 along and 1 down
        self.cut_range((1, 1), (1, 1))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is not rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=A2:A3')


    def test_copied_cellrange_reference_to_completely_copied_cellrange_is_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing A2:A3
        self.enter_cell_text(1, 1, '=A2:A3')
        self.wait_for_cell_to_contain_formula(1, 1, '=A2:A3')

        # * He uses copy & paste to move the formula, but not its dependencies,
        #   2 along and 1 down
        self.copy_range((1, 1), (1, 3))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is sensibly rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=C3:C4')


    def test_copied_cellrange_reference_to_partially_copied_cellrange_is_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing A2:A3
        self.enter_cell_text(1, 1, '=A2:A3')
        self.wait_for_cell_to_contain_formula(1, 1, '=A2:A3')

        # * He uses copy & paste to move the formula, but not its dependencies,
        #   2 along and 1 down
        self.copy_range((1, 1), (1, 2))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is sensibly rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=C3:C4')


    def test_copied_cellrange_reference_to_uncopied_cellrange_is_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing A2:A3
        self.enter_cell_text(1, 1, '=A2:A3')
        self.wait_for_cell_to_contain_formula(1, 1, '=A2:A3')

        # * He uses copy & paste to move the formula, but not its dependencies,
        #   2 along and 1 down
        self.copy_range((1, 1), (1, 1))
        self.paste_range((3, 2))
        self.wait_for_spinner_to_stop()

        # * He is please to see the formula is sensibly rewritten
        self.wait_for_cell_to_contain_formula(3, 2, '=C3:C4')


    def test_outside_cell_references_to_range_cut_from_ARE_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing B2
        self.enter_cell_text(1, 1, '=B2')
        self.wait_for_cell_to_contain_formula(1, 1, '=B2')

        # * He uses cut & paste to move the cell B2,
        # which A1 used to point to
        # to position C3
        self.cut_range((2, 2), (2, 2))
        self.paste_range((3, 3))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in A1
        # now points to the new location
        self.wait_for_cell_to_contain_formula(1, 1, '=C3')


    def test_outside_cell_ranges_pointing_inside_range_cut_from_ARE_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1, referencing B2:C3
        self.enter_cell_text(1, 1, '=B2:C3')
        self.wait_for_cell_to_contain_formula(1, 1, '=B2:C3')

        # * He uses cut & paste to move the B2:B3
        # which A1 used to point to
        # 3 across and 4 down
        self.cut_range((2, 2), (4, 4))
        self.paste_range((5, 6))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in A1
        # now points to the new location
        self.wait_for_cell_to_contain_formula(1, 1, '=E6:F7')


    def test_absolute_references_in_copied_range_to_outside_are_not_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing $A$1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=$A$1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=$A$1+1')

        # * Copies and pastes A2 to B2
        self.copy_range((1, 2), (1, 2))
        self.paste_range((2, 2))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B2 is the same as the one
        #   in A2.
        self.wait_for_cell_to_contain_formula(2, 2, '=$A$1+1')


    def test_absolute_references_in_copied_range_to_inside_are_not_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing $A$1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=$A$1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=$A$1+1')

        # * Copies and pastes A1:A2 to B1:B2
        self.copy_range((1, 1), (1, 2))
        self.paste_range((2, 1))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B2 is the same as the one
        #   in A2.
        self.wait_for_cell_to_contain_formula(2, 2, '=$A$1+1')


    def test_absolute_references_outside_copied_range_to_inside_are_not_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing $A$1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=$A$1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=$A$1+1')

        # * Copies and pastes A1 to B1
        self.copy_range((1, 1), (1, 1))
        self.paste_range((2, 1))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in A2 is unchanged
        self.wait_for_cell_to_contain_formula(1, 2, '=$A$1+1')


    def test_absolute_references_in_cut_range_to_outside_are_not_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing $A$1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=$A$1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=$A$1+1')

        # * Cut and pastes A2 to B2
        self.cut_range((1, 2), (1, 2))
        self.paste_range((2, 2))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B2 is the same as the one
        #   in A2.
        self.wait_for_cell_to_contain_formula(2, 2, '=$A$1+1')


    def test_absolute_references_in_cut_range_to_inside_are_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing $A$1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=$A$1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=$A$1+1')

        # * Cut and pastes A1:A2 to B1:B2
        self.cut_range((1, 1), (1, 2))
        self.paste_range((2, 1))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B2 is properly rewritten
        self.wait_for_cell_to_contain_formula(2, 2, '=$B$1+1')


    def test_absolute_references_outside_cut_range_to_inside_are_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing $A$1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=$A$1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=$A$1+1')

        # * Cut and pastes A1 to B1
        self.cut_range((1, 1), (1, 1))
        self.paste_range((2, 1))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B2 is rewritten
        self.wait_for_cell_to_contain_formula(1, 2, '=$B$1+1')


    def test_column_absolute_references_are_partially_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing $A1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=$A1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=$A1+1')

        # * Copies and pastes A2 to B3
        self.copy_range((1, 2), (1, 2))
        self.paste_range((2, 3))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B3 has been rewritten to
        #   refer to $A2
        self.wait_for_cell_to_contain_formula(2, 3, '=$A2+1')


    def test_row_absolute_references_are_partially_rewritten(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing A$1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=A$1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=A$1+1')

        # * Copies and pastes A2 to B3
        self.copy_range((1, 2), (1, 2))
        self.paste_range((2, 3))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B3 has been rewritten to
        #   refer to B$1.
        self.wait_for_cell_to_contain_formula(2, 3, '=B$1+1')


    def test_cell_rewrites_that_go_off_grid_are_handled(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A2, referencing A1
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '=A1+1')
        self.wait_for_cell_to_contain_formula(1, 2, '=A1+1')

        # * Copies and pastes A2 to B1
        self.copy_range((1, 2), (1, 2))
        self.paste_range((2, 1))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B1
        #   has an error message
        self.wait_for_cell_to_contain_formula(2, 1, '=#Invalid!+1')


    def test_cellrange_rewrites_that_go_off_grid_are_handled(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A3, referencing A1:A2
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '2')
        self.enter_cell_text(1, 3, '=sum(A1:A2)')
        self.wait_for_cell_to_contain_formula(1, 3, '=sum(A1:A2)')

        # * Copies and pastes A3 to B2
        self.copy_range((1, 3), (1, 3))
        self.paste_range((2, 2))
        self.wait_for_spinner_to_stop()

        # * He is pleased to see the formula in B2
        #   has an error message
        self.wait_for_cell_to_contain_formula(2, 2, '=sum(#Invalid!:B1)')


    def test_cut_paste_paste_rewrites_formulae_for_2nd_paste(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1
        self.enter_cell_text(1, 1, '=B1')

        # He pastes elsewhere, then pastes again
        self.cut_range((1, 1), (1, 1))
        self.paste_range((1, 2))
        self.paste_range((1, 3))
        self.wait_for_spinner_to_stop()

        # * the first paste (from a cut) does not rewrite the formula
        self.wait_for_cell_to_contain_formula(1, 2, '=B1')
        # * the second paste should act like a copy from the first paste
        self.wait_for_cell_to_contain_formula(1, 3, '=B2')


    def test_copy_paste_paste_always_rewrites_formulae(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold creates a formula in A1
        self.enter_cell_text(1, 1, '=B1')

        # He pastes elsewhere, then pastes again
        self.copy_range((1, 1), (1, 1))
        self.paste_range((1, 2))
        self.paste_range((1, 3))
        self.wait_for_spinner_to_stop()

        # * the first paste (from a copy) does rewrite the formula
        self.wait_for_cell_to_contain_formula(1, 2, '=B2')
        # * the second paste should act like a copy from the first paste
        self.wait_for_cell_to_contain_formula(1, 3, '=B3')


    def test_buttons(self):
        pass # *TODO we need cut, copy and paste buttons

