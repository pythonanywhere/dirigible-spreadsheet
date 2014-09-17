# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, Url

from textwrap import dedent


class Test_2622_CellRanges(FunctionalTest):

    def test_can_use_cell_ranges_in_usercode(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * While perusing the documentation, he notices a reference to cell ranges.
        sheet_url = self.browser.current_url
        self.go_to_url(Url.API_DOCS)
        self.wait_for_element_to_appear("id=CellRange")
        self.wait_for_element_to_appear("id=Worksheet.cell_range")

        # * Fascinated by this leap forward in the API, he creates a cellrange object in usercode
        self.go_to_url(sheet_url)
        self.wait_for_grid_to_appear()
        self.append_usercode(dedent('''
            worksheet.B3.value = 1
            worksheet.C3.value = 2
            worksheet.D3.value = 'outside'
            worksheet.B4.value = 3
            #worksheet C4 is blank
            worksheet.B5.value = 5
            worksheet.C5.value = 6
            #worksheet row 6 is blank
            worksheet.B7.value = 'a random string in the middle'
            worksheet.C7.value = 10

            my_range_no_blanks = worksheet.cell_range('B3:B5')
            cells_total = sum(my_range_no_blanks)
            worksheet.A1.value = cells_total

            my_full_range_syntax1 = worksheet.cell_range('B3','C10')
            for col, value in enumerate(my_full_range_syntax1):
                worksheet[col+2, 1].value = value

            my_full_range_syntax2 = worksheet.cell_range((2,3),'C10')
            for col, cell in enumerate(my_full_range_syntax2.cells):
                worksheet[col+2, 2].value = cell.value
        '''))

        self.wait_for_cell_value(1, 1, '9')

        data1 = [1,2,3,'',5,6,'','','a random string in the middle',10]
        for col, value in enumerate(data1):
            self.wait_for_cell_value(col+2, 1, str(value))

        for col, value in enumerate(data1):
            self.wait_for_cell_value(col+2, 2, str(value))


    def test_can_use_cell_ranges_in_formulae(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '2')
        self.enter_cell_text(1, 3, '3')
        self.enter_cell_text(2, 1, '=sum(A1:A3)')

        self.wait_for_cell_value(2, 1, '6')


    def test_bare_cell_ranges_in_cells_dont_cause_recursive_explosion(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(1, 2, '2')
        self.enter_cell_text(1, 3, '3')
        self.enter_cell_text(2, 1, '=A1:A3')

        self.wait_for_cell_value(2, 1, "<CellRange A1 to A3 in <Worksheet>>")


    def test_cellrange_dependencies(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * he creates many cell formulae
        self.prepend_usercode(dedent('''
            for col in range(2, 12):
              for row in range(2, 12):
                worksheet[col, row].formula = '=1'
            worksheet[1, 1].formula = '=sum(b2:k11)'
        '''))
        # * the sum in a1 ought to be calculated after all
        #   the other cell formulae
        self.wait_for_cell_value(1, 1, '100')

