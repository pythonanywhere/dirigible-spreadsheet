# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

from os import path
import urllib2
from urlparse import urljoin

from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT


class Test_2774_ExportCSV(FunctionalTest):

    def test_can_export_csv(self):
        # * Harold logs in to Dirigible and creates a nice shiny new sheet
        sheet_id = self.login_and_create_new_sheet()

        # * He puts some data including formulae and usercode-calculated stuff into a spreadsheet.
        #   Some of the data has commas and the like in it, and there is a blank column to the
        #   left of the data and a blank row above it.  There are also non-string cell contents.
        self.enter_cell_text(2, 2,
                "Data at A2, from a constant")
        self.enter_cell_text(2, 3,
                "Data at A3, with a \\n that might need escaping")
        self.enter_cell_text(2, 4,
                "Data at A4, with 'single quotes'")
        self.enter_cell_text(2, 5,
                'Data at A5, with "double quotes"')
        self.enter_cell_text(2, 6,
                u'Data at A6, with some unicode: Sacr\xe9 bleu! The \xa3 is expensive, compared to the \u20ac!')
        self.enter_cell_text(3, 2, "=2+2")
        self.append_usercode("worksheet.E4.value = 'hellooooo there!'")
        self.append_usercode(
                "worksheet.E5.value = ['list item 1', 'list item 2', 3]")
        self.append_usercode(
                "worksheet.E6.value = {'oats': 'a cereal which in England is fed to horses, but in Scotland forms the sustenance of the nation'}")
        self.append_usercode(
                "worksheet.E7.value = lambda x : 2 * x")

        self.wait_for_spinner_to_stop()

        # * He sees a button that talks about exporting CSVs
        self.wait_for_element_visibility('id=id_export_button', True)
        self.assertEquals(
                self.selenium.get_attribute('id=id_export_button@alt'),
                "Download as CSV file"
        )
        self.assertEquals(
                self.selenium.get_attribute('id=id_export_button@title'),
                "Download as CSV file"
        )
        # * He clicks on it, and sees a popup dialog with two links and a close button
        self.selenium.click('id=id_export_button')
        self.wait_for_element_visibility('id=id_export_dialog', True)
        self.wait_for_element_visibility('id=id_export_csv_excel_version', True)
        self.wait_for_element_visibility('id=id_export_csv_unicode_version', True)
        self.wait_for_element_visibility('id=id_export_dialog_close_button', True)
        self.assertEquals(self.selenium.get_value('id=id_export_dialog_close_button'), "Close")

        # Were he to click on the former, his browser would do whatever it normally
        # does when a user starts a download. This is too hard to test with
        # Selenium.  Lets go shopping^W^W use urllib2
        download_url = self.selenium.get_attribute('id=id_export_csv_excel_version@href')
        download_url = urljoin(self.browser.current_url, download_url)

        stream = self.get_url_with_session_cookie(download_url)
        self.assertEquals(stream.info().gettype(), "text/csv")
        sheet_name = 'Sheet %s' % (sheet_id,)
        self.assertEquals(
                stream.info()['Content-Disposition'],
                'attachment; filename=%s.csv' % (sheet_name,)
        )

        expected_file_name = path.join(
                path.dirname(__file__),
                "test_data", "expected_csv_file.csv"
        )
        with open(expected_file_name) as expected_file:
            self.assertEquals(
                stream.read().replace("\r\n", "\n"),
                expected_file.read().replace("\r\n", "\n")
            )

        # The file downloaded, he closes the dialog.
        self.selenium.click('id=id_export_dialog_close_button')
        self.wait_for_element_visibility('id=id_export_dialog', False)



    def test_can_export_unicode(self):
        #Harold-san has a sheet-u-des which has some zugoi kanji in:
        sheet_id = self.login_and_create_new_sheet()
        some_kanji = u'\u30bc\u30ed\u30a6\u30a3\u30f3\u30b0'
        self.enter_cell_text(1, 1, some_kanji)
        self.wait_for_spinner_to_stop()

        page_url = self.browser.current_url

        # * He clicks on a button that clearly allows him to export CSV data.
        self.wait_for_element_visibility('id=id_export_button', True)

        # * He clicks on it, and sees a popup dialog with two links
        self.selenium.click('id=id_export_button')
        self.wait_for_element_visibility('id=id_export_dialog', True)
        self.wait_for_element_visibility('id=id_export_csv_excel_version', True)
        self.wait_for_element_visibility('id=id_export_csv_unicode_version', True)

        # * He likes excel, so he tries to download the excel version
        self.click_link('id_export_csv_excel_version')

        # He is taken to an error page, with a helpful message suggesting he
        # tries again using the international version
        self.assertEquals(self.selenium.get_title(), "CSV Export Error: Dirigible")
        self.assertEquals(
            self.selenium.get_text("id=id_server_error_title"),
            "Could not export CSV file"
        )
        error_text = self.selenium.get_text("id=id_server_error_text")
        msg = "Sorry, your spreadsheet contains characters that cannot be saved in Excel CSV format"
        self.assertTrue(msg in error_text)
        msg = "Please try again using the international version"
        self.assertTrue(msg in error_text)


        # * He notes there is a link back to the sheet page
        self.wait_for_element_visibility('id=id_sheet_link', True)

        # * But he spots a helpful link to the documentation, which he follows
        self.selenium.click('css=a[href="/documentation/import_export.html"]')
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.assertTrue(
                'Importing and Exporting' in self.selenium.get_title()
        )

        # He goes back to his sheet page
        self.selenium.open(page_url)
        self.wait_for_grid_to_appear()

        # * And tries his export again
        self.selenium.click('id=id_export_button')

        # test unicode download
        download_url = self.selenium.get_attribute('id=id_export_csv_unicode_version@href')
        download_url = urljoin(self.browser.current_url, download_url)

        opener = urllib2.build_opener()
        session_cookie = self.selenium.get_cookie_by_name('sessionid')
        opener.addheaders.append(('Cookie', 'sessionid=%s' % (session_cookie, )))
        stream = opener.open(download_url)
        self.assertEquals(stream.info().gettype(), "text/csv")
        sheet_name = 'Sheet %s' % (sheet_id,)
        self.assertEquals(
                stream.info()['Content-Disposition'],
                'attachment; filename=%s.csv' % (sheet_name,)
        )

        expected_file_name = path.join(
                path.dirname(__file__),
                "test_data", "expected_unicode_csv.csv"
        )
        with open(expected_file_name) as expected_file:
            self.assertEquals(
                stream.read().replace("\r\n", "\n"),
                expected_file.read().replace("\r\n", "\n")
            )
