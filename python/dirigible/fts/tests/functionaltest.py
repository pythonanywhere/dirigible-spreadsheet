# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

import datetime
from email.parser import Parser
from functools import wraps
import hashlib
import re
from textwrap import dedent
from threading import Thread
import time
import urllib
import urllib2
from urlparse import urljoin, urlparse, urlunparse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver

# Only used on Windows for the test run, but we need to be able to
# import the module on nell in order to create the users for the
# FTs.
try:
    import SendKeys
except:
    pass

import key_codes

IMAP_HOST = ""
IMAP_USERNAME = ""
IMAP_PASSWORD = ""

PAGE_LOAD_TIMEOUT = 10000
DEFAULT_WAIT_FOR_TIMEOUT = 10
USER_PASSWORD = 'p4ssw0rd'

CURRENT_API_VERSION = '0.1'


class Url(object):
    ROOT = 'http://localhost:8081/'
    LOGIN = urljoin(ROOT, '/login/')
    LOGOUT = urljoin(ROOT, '/logout')
    NEW_SHEET = urljoin(ROOT, '/new_sheet')
    SIGNUP = urljoin(ROOT, '/signup/register/')
    DOCUMENTATION = urljoin(ROOT, '/documentation/')
    API_DOCS = urljoin(DOCUMENTATION, 'builtins.html')


    @classmethod
    def user_page(cls, username):
        return urljoin(Url.ROOT, '/user/%s/' % (username,))

    @classmethod
    def sheet_page(cls, username, sheet_id):
        return urljoin(cls.user_page(username), 'sheet/%s/' % (sheet_id,))

    @classmethod
    def api_url(cls, username, sheet_id):
        return urljoin(cls.sheet_page(username, sheet_id), 'v%s/json/' % (CURRENT_API_VERSION,))


import os
SCREEN_DUMP_LOCATION = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'screendumps')
)

def snapshot_on_error(test):

    @wraps(test)
    def inner(*args, **kwargs):
        try:
            test(*args, **kwargs)
        except:
            test_object = args[0]

            try:
                timestamp = datetime.datetime.now().isoformat().replace(':', '.')[:19]
                filename = '{folder}/{test_id}-{timestamp}.png'.format(
                    folder=SCREEN_DUMP_LOCATION,
                    test_id=test_object.id(),
                    timestamp=timestamp
                )
                print('screenshot to {}'.format(filename))
                test_object.browser.get_screenshot_as_file(filename)
            except:
                pass

            raise
    return inner


def humanesque_delay(length=0.2):
    time.sleep(length)


def humanise_with_delay(action):
    @wraps(action)
    def inner(*args, **kwargs):
        humanesque_delay()
        result = action(*args, **kwargs)
        humanesque_delay()
        return result
    return inner


class Bounds(object):
    def __init__(self, width, height, top, left):
        self.width = width
        self.height = height
        self.top = top
        self.left = left

    bottom = property(lambda self: self.top + self.height)

    right = property(lambda self: self.left + self.width)


RGB_RE = re.compile('^rgba?\((\d+), (\d+), (\d+)(, (\d+))?\)')

def convert_rgb_to_hex(value):
    match = RGB_RE.match(value)
    r, g, b = match.group(1), match.group(2), match.group(3)
    return '#%X%X%X' % (int(r), int(g), int(b))


class FunctionalTest(StaticLiveServerTestCase):
    user_count = 1

    def wait_for(self, condition_function, msg_function, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT, allow_exceptions=False):
        start = time.clock()
        end = start + timeout_seconds
        exception_raised = False
        tries = 0
        while tries < 2 or time.clock() < end:
            try:
                tries += 1
                if condition_function():
                    return
                exception_raised = False
            except Exception, e:
                if not allow_exceptions:
                    raise e
                exception_raised = True
            time.sleep(0.1)
        if exception_raised:
            raise
        self.fail("Timeout waiting for condition: %s" % (msg_function(),))


    @humanise_with_delay
    def human_key_press(self, key_code):
        self.selenium.key_press_native(key_code)


    def key_down(self, key_code):
        test = self
        class _Inner(object):
            @humanise_with_delay
            def __enter__(self):
                test.selenium.key_down_native(key_code)

            @humanise_with_delay
            def __exit__(self, exc_type, exc_value, exc_traceback):
                test.selenium.key_up_native(key_code)
        return _Inner()


    def click_to_and_blur_from(self, click_to_locator, blur_from_locator):
        self.selenium.fire_event(blur_from_locator, 'blur')
        self.selenium.click(click_to_locator)


    def get_element_bounds(self, locator):
        return Bounds(
            self.selenium.get_element_width(locator),
            self.selenium.get_element_height(locator),
            self.selenium.get_element_position_top(locator),
            self.selenium.get_element_position_left(locator)
        )


    def get_css_property(self, jquery_locator, property_name):
        property_value = self.selenium.get_eval('window.$("%s").css("%s")' % (jquery_locator, property_name))
        if property_value == 'rgba(0, 0, 0, 0)': # transparent in chrome
            return 'transparent'
        if property_value.startswith('rgb'):
            property_value = convert_rgb_to_hex(property_value)
        if property_value.startswith('#'):
            property_value = property_value.upper()
            if len(property_value) == 4:
                _, r, g, b = property_value
                property_value = '#%s%s%s%s%s%s' % (r, r, g, g, b, b)
        return property_value


    def assert_urls_are_same(self, actual, expected):
        loc = self.selenium.get_location()
        canonicalised_actual = urljoin(loc, actual)
        canonicalised_expected = urljoin(loc, expected)
        self.assertEquals(canonicalised_actual, canonicalised_expected)


    def assert_HTTP_error(self, url, error_code):
        try:
            self.selenium.open(url)
        except Exception, e:
            if ('Response_Code = %d' % (error_code,)) in str(e):
                self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
            else:
                raise e
        else:
            self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
            possible_error_locators = ('id=summary', 'id=id_server_error_title')
            for error_locator in possible_error_locators:
                if self.selenium.is_element_present(error_locator) and str(error_code) in self.selenium.get_text(error_locator):
                    return
            self.fail('%d not raised, got: %s' % (error_code, self.selenium.get_title()))


    def assert_redirects(self, from_url, to_url):
        self.go_to_url(from_url)
        self.assert_urls_are_same(
            urlunparse(urlparse(self.selenium.get_location())[:4] + ('', '')),
            to_url
        )


    def is_element_focused(self, locator):
        if locator.startswith('css='):
            return self.selenium.get_eval('window.document.activeElement == window.$("%s")[0]' % (locator[4:],)) == 'true'
        elif locator.startswith('id='):
            return self.selenium.get_eval('window.document.activeElement == window.document.getElementById("%s")' % (locator[3:],)) == 'true'
        else:
            raise ValueError('invalid locator')


    def is_element_enabled(self, element_id):
        #self.selenium.get_attribute is unreliable (Harry, Jonathan)
        disabled = self.selenium.get_eval('window.$("#%s").attr("disabled")' % (element_id,))
        return disabled not in ("true", "disabled")


    def wait_for_element_presence(
           self, locator, present=True, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT
    ):
        if present:
            failure_message = "Element %s to be present" % (locator, ),
        else:
            failure_message = "Element %s to not exist" % (locator, ),
        self.wait_for(
            lambda : present == self.selenium.is_element_present(locator),
            lambda : failure_message,
            timeout_seconds=timeout_seconds
        )


    def wait_for_element_to_appear(self, locator, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for_element_presence(locator, True, timeout_seconds)


    def wait_for_element_text(self, locator, text, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for(
            lambda : self.selenium.get_text(locator) == text,
            lambda : "Element %s to contain text %r. Contained %r" % (locator, text, self.selenium.get_text(locator)),
            timeout_seconds=timeout_seconds
        )


    def wait_for_element_visibility(self, locator, visibility, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for(
            lambda : self.selenium.is_visible(locator) == visibility,
            lambda : "Element %s to become%svisible" % (locator, visibility and ' ' or ' in'),
            timeout_seconds=timeout_seconds
        )


    def create_users(self):
        from django.contrib.auth.models import User
        for username in self.get_my_usernames():
            user = User.objects.create(username=username)
            user.set_password('p4ssw0rd')
            user.save()
            profile = user.get_profile()
            profile.has_seen_sheet_page = True
            profile.save()

    def setUp(self):
        print "%s ##### Running test %s" % (datetime.datetime.now(), self.id())
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(2)


    def tearDown(self):
        try:
            self.logout()
        finally:
            self.browser.quit()
            print "%s ##### Finished test %s" % (datetime.datetime.now(), self.id())


    def login(self, username=None, password=USER_PASSWORD, already_on_login_page=False):
        if username is None:
            username = self.get_my_username()
        if not already_on_login_page:
            self.go_to_url(Url.LOGIN)
        self.selenium.type('id=id_username', username)
        self.selenium.type('id=id_password', password)
        self.click_link('id_login')


    def logout(self):
        self.go_to_url(Url.LOGOUT)


    def get_url_with_session_cookie(self, url, data=None):
        opener = urllib2.build_opener()
        session_cookie = self.selenium.get_cookie_by_name('sessionid')
        opener.addheaders.append(('Cookie', 'sessionid=%s' % (session_cookie, )))
        if data is None:
            return opener.open(url)
        else:
            encoded_data = urllib.urlencode(data)
            return opener.open(url, encoded_data)


    def create_new_sheet(self, username=None, already_on_dashboard=False):
        if username is None:
            username = self.get_my_username()
        if not already_on_dashboard:
            self.go_to_url(Url.user_page(username))

        self.click_link('id_create_new_sheet')
        self.wait_for_grid_to_appear()

        location = self.selenium.get_location()
        sheet_id = re.search('/sheet/([0-9]+)/', location).group(1)
        return sheet_id


    def login_and_create_new_sheet(self, username=None):
        self.login(username=username)
        return self.create_new_sheet(username=username)


    def get_my_usernames(self):
        usernames = []
        for user_index in range(self.user_count):
            capture_test_details = re.compile(r'test_(\d+)_[^\.]*\.[^\.]*\.test_(.*)$')
            match = re.search(capture_test_details, self.id())
            test_task_id = match.group(1)
            test_method_name = match.group(2)
            test_method_hash = hashlib.md5(test_method_name).hexdigest()[:7]

            usernames.append(("%s_%s" % (test_task_id, test_method_hash))[:29] + str(user_index))
        return usernames


    def get_my_username(self):
        return self.get_my_usernames()[0]


    def _check_page_link_home(self):

        if self.browser.current_url.startswith(Url.DOCUMENTATION):
            return

        link = None
        for possible_link_image in ('id_big_logo', 'id_small_header_logo'):
            try:
                link = self.browser.find_element_by_xpath(
                    "//a[img[@id='{img_id}']]@href".format(
                        img_id=possible_link_image
                    )
                )
            except:
                pass
            else:
                break
        if link is None:
            self.fail(
                "Could not find a logo that is also a link on page {}".format(
                    self.browser.current_url
                )
            )
        self.assertTrue(link in ("/", Url.ROOT))


    def check_page_load(self, link_destination=None):
        self._check_page_link_home()


    def go_to_url(self, url):
        self.browser.get(url)
        self.check_page_load(url)


    def refresh_sheet_page(self):
        self.selenium.refresh()
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.wait_for_grid_to_appear()


    def click_link(self, element_id):
        self.selenium.click('id=%s' % (element_id,))
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.check_page_load()


    def set_sheet_name(self, name):
        self.selenium.click('id=id_sheet_name')
        self.wait_for(
            lambda: self.selenium.is_element_present('id=edit-id_sheet_name'),
            lambda: 'editable sheetname to appear')
        self.selenium.type('id=edit-id_sheet_name', name)
        self.human_key_press(key_codes.ENTER)
        self.wait_for(
            lambda: self.selenium.get_text('id=id_sheet_name') == name,
            lambda: 'sheet name to be updated'
        )


    def assert_sends_to_login_page(self, requested_url):
        self.assert_redirects(requested_url, Url.LOGIN)


    def assert_sends_to_root_page(self, requested_url):
        self.assert_redirects(requested_url, Url.ROOT)


    def assert_page_title_contains(self, link_url, title):
        original_page = self.selenium.get_location()
        self.go_to_url(link_url)
        self.assertTrue(title in self.selenium.get_title())
        self.go_to_url(original_page)


    def assert_has_useful_information_links(self):
        self.assert_page_title_contains(
            self.selenium.get_attribute("xpath=//a[text() = 'Terms & Conditions']@href"),
            'Terms and Conditions: Dirigible'
        )
        self.assert_page_title_contains(
            self.selenium.get_attribute("xpath=//a[text() = 'Privacy Policy']@href"),
            'Privacy: Dirigible'
        )
        self.assert_page_title_contains(
            self.selenium.get_attribute("xpath=//a[text() = 'Contact Us']@href"),
            'Contact: Dirigible'
        )


    def get_cell_css(self, column, row, must_be_active=False):
        active_classes = ''
        if must_be_active:
            active_classes = '.active'
        return 'div.slick-row[row=%d] div.slick-cell.c%d%s' % (
            row - 1, column, active_classes)


    def get_cell_locator(self, column, row, must_be_active=False):
        return 'css=%s' % (self.get_cell_css(column, row, must_be_active),)


    def get_cell_formatted_value_locator(self, column, row, raise_if_cell_missing=True):
        cell_css = self.get_cell_css(column, row)
        if not self.selenium.is_element_present('css=%s' % (cell_css,)):
            if raise_if_cell_missing:
                raise Exception("Cell not present at %s, %s" % (column, row))
            else:
                return None
        return 'css=%s span.grid_formatted_value' % (cell_css,)



    def get_cell_editor_css(self):
        return 'input.editor-text'


    def get_active_cell_editor_locator(self):
        return 'css=%s' % (self.get_cell_editor_css())


    def get_cell_editor_locator(self, column, row):
        cell_css = self.get_cell_css(column, row)
        editor_css = self.get_cell_editor_css()
        return 'css=%s %s' % (cell_css, editor_css)


    def is_cell_visible(self, column, row):
        tries = 0
        while tries < 4:
            try:
                return 'true' == self.selenium.get_eval(dedent(
                    '''
                        (function () {
                            var viewport = window.grid.getViewport();
                            if (viewport.top > %(row)s || %(row)s > viewport.bottom) {
                                return false;
                            }

                            var $canvasDiv = window.$('div.grid-canvas');
                            var $viewportDiv = window.$('div.slick-viewport');
                            var viewableLeft = -$canvasDiv.position().left;
                            var viewableRight = viewableLeft + $viewportDiv.width();
                            var $currentCell = window.$('%(current_cell_css)s');
                            var currentCellLeft = $currentCell.position().left;
                            var currentCellRight = currentCellLeft + $currentCell.outerWidth();
                            if (viewableLeft > currentCellLeft || currentCellRight > viewableRight) {
                                return false;
                            }

                            return true;
                        })()
                    ''' % dict(row=row, col=column, current_cell_css=self.get_cell_css(column, row) )
                ) )
            except:
                time.sleep(1)
                tries += 1

        self.fail("Could not check for cell visibility at %s, %s after %s tries" % (column, row, tries))


    def assert_cell_visible(self, column, row):
        self.assertTrue(
            self.is_cell_visible(column, row),
            'cell %s, %s not visible' % (column, row)
        )


    def wait_for_cell_to_be_visible(self, column, row, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for(
            lambda : self.is_cell_visible(column, row),
            lambda : "Cell at %s, %s to become visible" % (column, row),
            allow_exceptions=True,
            timeout_seconds=timeout_seconds
        )


    def get_formula_bar_id(self):
        return "id_formula_bar"


    def get_formula_bar_locator(self):
        return "id=%s" % (self.get_formula_bar_id(),)


    def is_formula_bar_enabled(self):
        return self.is_element_enabled(self.get_formula_bar_id())


    def scroll_cell_row_into_view(self, column, row):
        self.selenium.get_eval(
            'window.grid.scrollRowIntoView(%s, true)' % (row - 1,))
        self.wait_for_element_to_appear(self.get_cell_locator(column, row))


    def go_to_cell(self, column, row):
        self.selenium.get_eval(
            'window.grid.gotoCell(%s, %s, false)' % (row - 1, column))
        self.wait_for_element_to_appear(self.get_cell_locator(column, row))


    @humanise_with_delay
    def click_on_cell(self, column, row):
        self.go_to_cell(column, row)
        self.selenium.click(self.get_cell_locator(column, row))
        # We previously had code to focus() the cell here, please don't re-introduce
        # -- it breaks test #2633 on IE.


    def select_range_with_shift_click(self, start, end):
        self.click_on_cell(*start)
        with self.key_down(key_codes.SHIFT):
            self.click_on_cell(*end)
        self.assert_current_selection(start, end)


    def mouse_drag(self, cell_from, cell_to):
        from_locator = self.get_cell_locator(*cell_from)
        to_locator = self.get_cell_locator(*cell_to)

        pixel_offset = "10,30"
        #pixel offset fixes selenium weird tendency to click too far north-west.
        #may cause problems if column widths are reduced...

        self.selenium.mouse_down_at(from_locator, pixel_offset)
        humanesque_delay(1)
        self.selenium.mouse_move_at(from_locator, pixel_offset)
        humanesque_delay(1)
        self.selenium.mouse_move_at(to_locator, pixel_offset)
        humanesque_delay(1)
        self.selenium.mouse_up_at(to_locator, pixel_offset)
        humanesque_delay(1)


    def assert_current_selection(self, topleft, bottomright, thoroughly=True):
        if thoroughly:
            for row in range(topleft[1],bottomright[1] + 1):
                for col in range(topleft[0],bottomright[0] + 1):
                    locator = self.get_cell_locator(col, row) + '.selected'
                    self.wait_for_element_to_appear(locator)
        else:
            topleft_locator = self.get_cell_locator(*topleft) + '.selected'
            bottomright_locator = (
                self.get_cell_locator(*bottomright) + '.selected'
            )
            self.wait_for_element_to_appear(topleft_locator)
            self.wait_for_element_to_appear(bottomright_locator)


    @humanise_with_delay
    def open_cell_for_editing(self, column, row):
        self.scroll_cell_row_into_view(column, row)
        self.wait_for_element_to_appear(self.get_cell_locator(column, row))
        self.selenium.double_click(self.get_cell_locator(column, row))
        self.selenium.focus(self.get_active_cell_editor_locator())


    def type_into_cell_editor_unhumanized(self, text):
        retries = 0
        while self.get_cell_editor_content() != text:
            if retries > 10:
                self.fail("Selenium could not type something in to a text field, no matter how hard it tried")
            self.selenium.type('css=input.editor-text', text)
            retries += 1


    @humanise_with_delay
    def enter_cell_text(self, col, row, text):
        self.enter_cell_text_unhumanized(col, row, text)


    def enter_cell_text_unhumanized(self, col, row, text):
        self.open_cell_for_editing(col, row)
        self.wait_for_cell_to_enter_edit_mode(col, row)
        self.type_into_cell_editor_unhumanized(text)
        self.selenium.key_press_native(key_codes.ENTER)


    def get_current_cell(self):
        row = int(self.selenium.get_eval(
            'window.grid.getActiveCell().row')
        ) + 1
        column = int(self.selenium.get_eval(
            'window.grid.getActiveCell().cell'
        ))
        return column, row


    def get_cell_text(self, column, row):
        self.scroll_cell_row_into_view(column, row)
        return self.selenium.get_text(self.get_cell_locator(column, row))


    def get_cell_editor_content(self):
        return self.selenium.get_value(self.get_active_cell_editor_locator())


    def get_cell_shown_formula_locator(self, column, row, raise_if_cell_missing=True):
        cell_css = self.get_cell_css(column, row)
        if not self.selenium.is_element_present('css=%s' % (cell_css,)):
            if raise_if_cell_missing:
                raise Exception("Cell not present at %s, %s" % (column, row))
            else:
                return None
        return 'css=%s span.grid_formula' % (cell_css,)


    def get_cell_shown_formula(self, column, row, raise_if_cell_missing=True):
        formula_locator = self.get_cell_shown_formula_locator(column, row, raise_if_cell_missing)
        if not self.selenium.is_element_present(formula_locator):
            return None

        return self.selenium.get_text(formula_locator)


    def assert_cell_shown_formula(self, column, row, formula):
        self.assertEquals(self.get_cell_shown_formula(column, row), formula)


    def wait_for_cell_shown_formula(self, column, row, formula, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        def generate_failure_message():
            return (
                "cell %d, %d to show formula '%s', was %r -- text is %r" % (
                column, row, formula, self.get_cell_shown_formula(column, row), self.get_cell_text(column, row))
            )

        self.wait_for(
            lambda : self.get_cell_shown_formula(column, row, raise_if_cell_missing=False) == formula,
            generate_failure_message,
            allow_exceptions=True,
            timeout_seconds=timeout_seconds
        )


    def wait_for_cell_to_contain_formula(self, column, row, formula):
        self.open_cell_for_editing(column, row)
        self.wait_for_cell_editor_content(formula)
        self.human_key_press(key_codes.ENTER)


    def get_cell_error(self, column, row):
        error_img_id = 'id_%d_%d_error' % (column, row)
        if self.selenium.is_element_present('id=%s' % (error_img_id,)):
            return self.selenium.get_attribute('id=%s@title' % (error_img_id,))


    def assert_cell_has_error(self, column, row, error_text):
        error_img_id = 'id_%d_%d_error' % (column, row)
        self.wait_for_element_to_appear('id=%s' % (error_img_id,) )
        self.assertEquals(self.get_cell_error(column, row), error_text)


    def assert_cell_has_no_error(self, column, row):
        error_img_id = 'id_%d_%d_error' % (column, row)
        self.assertFalse(self.selenium.is_element_present('id=%s' % (error_img_id,)),
                         'Error present for (%d, %d)' % (column, row))


    def assert_cell_is_current_but_not_editing(self, col, row):
        self.wait_for_cell_to_become_active(col, row)
        self.assertFalse(
            self.is_element_focused(self.get_cell_editor_locator(col, row))
        )


    def assert_cell_is_current_and_is_editing(self, col, row):
        self.wait_for_cell_to_become_active(col, row)
        self.assertTrue(
            self.is_element_focused(self.get_cell_editor_locator(col, row))
        )


    def wait_for_cell_value(self, column, row, value_or_regex, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        def match(text):
            if hasattr(value_or_regex, 'match'):
                return value_or_regex.match(text)
            else:
                return text == value_or_regex

        def cell_shows_value():
            self.last_found_value = self.get_cell_text(column, row)
            return (
                match(self.last_found_value) and
                self.get_cell_shown_formula(
                    column, row, raise_if_cell_missing=False
                ) is None
            )

        def generate_failure_message():
            actual_value = self.last_found_value
            self.last_found_value = None
            actual_formula = ''
            if self.get_cell_shown_formula(column, row) is not None:
                actual_formula = self.last_found_value
                actual_value = ''
            actual_error = self.get_cell_error(column, row)

            return (
                "Cell at (%s, %s) to become %r "
                "(value=%r, shown formula=%r, error=%r)" % (
                    column, row, value_or_regex,
                    actual_value, actual_formula, actual_error)
            )

        self.last_found_value = None
        self.wait_for(
            cell_shows_value,
            generate_failure_message,
            timeout_seconds=timeout_seconds,
            allow_exceptions=True
        )


    def wait_for_cell_to_become_active(self, column, row, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        locator = self.get_cell_locator(column,row, must_be_active=True)
        self.wait_for(
            lambda : self.selenium.is_element_present(locator),
            lambda : "Cell at (%s, %s) was not active. Selection is: %s" %
                (column, row, self.get_current_cell()),
            timeout_seconds=timeout_seconds
        )


    def wait_for_cell_to_enter_edit_mode(self, column, row, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for_cell_to_become_active(column, row)
        full_editor_locator = self.get_cell_editor_locator(column, row)
        self.wait_for(
            lambda : self.is_element_focused(full_editor_locator),
            lambda : "Editor at (%s, %s) to get focus" % (column, row),
            timeout_seconds=timeout_seconds
        )


    def wait_for_cell_editor_content(self, content):
        self.wait_for(
            lambda : self.get_cell_editor_content() == content,
            lambda : "Cell editor to become %s (was '%s')" % (content, self.get_cell_editor_content()),
        )


    def get_viewport_top(self):
        return int(self.selenium.get_eval(
            'window.grid.getViewport().top'
        ) ) + 1


    def get_viewport_bottom(self):
        return int(self.selenium.get_eval(
            'window.grid.getViewport().bottom'
        ) ) + 1


    def is_spinner_visible(self):
        return (
            self.selenium.is_element_present('css=#id_spinner_image')
            and not self.selenium.is_element_present('css=#id_spinner_image.hidden')
        )


    def wait_for_spinner_to_stop(self, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for(
            lambda : not self.is_spinner_visible(),
            lambda : "Spinner to disappear",
            timeout_seconds=timeout_seconds
        )


    def wait_for_grid_to_appear(self, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for_element_to_appear(self.get_cell_locator(1, 1), timeout_seconds)


    def get_usercode(self):
        return self.selenium.get_eval('window.editor.session.getValue()').replace('\r\n', '\n').strip()


    @humanise_with_delay
    def enter_usercode(self, code, commit_change=True):
        self.selenium.get_eval("window.editor.textInput.getElement().focus()")
        self.selenium.get_eval("window.editor.session.setValue(%s)"
                % (repr(unicode(code))[1:], )
        )
        if commit_change:
            ## We would just click away, but Selenium does not fire the full event stack
            ## for clicks.
            humanesque_delay()
            self.selenium.get_eval("window.editor.blur()")


    def append_usercode(self, code):
        self.enter_usercode("%s\n%s" % (self.get_usercode(), code))


    def prepend_usercode(self, code):
        self.enter_usercode("%s\n%s" % (code, self.get_usercode()))


    def wait_for_usercode_editor_content(self, content, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for(
            lambda : self.get_usercode() == content,
            lambda : 'Usercode editor content to become \n"%s"\n(was \n"%s"\n)' % (content, self.get_usercode()),
            timeout_seconds=timeout_seconds
        )


    def sanitise_console_content(self, content):
        # IE has char 13 for return instead of the normal Unix 10.
        # Not sure why it differs from Chrome and Firefox.
        return content.replace('\r', '\n')


    def get_console_content(self):
        content = self.selenium.get_eval('window.$("#id_console").text()')
        return self.sanitise_console_content(content)


    def wait_for_console_content(self, content, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for(
            lambda: content in self.get_console_content(),
            lambda : 'error console to contain "%s" (was "%s")' % (content, self.get_console_content()),
           timeout_seconds=timeout_seconds
        )


    def get_formula_bar_contents(self):
        return self.selenium.get_value(self.get_formula_bar_locator())


    def assert_formula_bar_contains(self, contents):
        self.assertEquals(self.get_formula_bar_contents(), contents)


    def wait_for_formula_bar_contents(self, contents, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT):
        self.wait_for(
            lambda : self.get_formula_bar_contents() == contents,
            lambda : 'formula bar to contain "%s" (was "%s")' % (contents, self.get_formula_bar_contents() ),
            timeout_seconds=timeout_seconds
        )

    def click_formula_bar(self):
        self.selenium.click(self.get_formula_bar_locator())
        self.wait_for(
            lambda : self.is_element_focused(self.get_formula_bar_locator()),
            lambda : "Formula bar to gain focus"
        )


    def copy_range(self, start, end):
        self.click_on_cell(*start)
        with self.key_down(key_codes.SHIFT):
            self.click_on_cell(*end)
        self.assert_current_selection(start, end)
        with self.key_down(key_codes.CTRL):
            self.selenium.key_press_native(key_codes.LETTER_C)


    def cut_range(self, start, end):
        self.click_on_cell(*start)
        with self.key_down(key_codes.SHIFT):
            self.click_on_cell(*end)
        self.assert_current_selection(start, end)
        with self.key_down(key_codes.CTRL):
            self.selenium.key_press_native(key_codes.LETTER_X)
        self.wait_for_spinner_to_stop()


    def paste_range(self, start, end=None):
        self.click_on_cell(*start)
        if end:
            with self.key_down(key_codes.SHIFT):
                self.click_on_cell(*end)
        with self.key_down(key_codes.CTRL):
            self.selenium.key_press_native(key_codes.LETTER_V)
        self.wait_for_spinner_to_stop()


    def set_filename_for_upload(self, file_name, field_selector):
        if self.selenium.browserStartCommand == '*firefox':
            self.selenium.focus(field_selector)
            self.selenium.type(field_selector, file_name)
            self.selenium.click(field_selector)
        else:
            def handle_file_dialog():
                time.sleep(2)
                SendKeys.SendKeys('{ENTER}')
                time.sleep(2)
                escaped_filename = file_name.replace('~','{~}')
                SendKeys.SendKeys(escaped_filename)
                SendKeys.SendKeys('{ENTER}')
                time.sleep(2)

            dialog_thread = Thread(target=handle_file_dialog)
            dialog_thread.start()
            self.selenium.click(field_selector)
            self.selenium.focus(field_selector)
            dialog_thread.join()


    def pop_email_for_client(self, email_address, fail_if_none=True, content_filter=None):
        retries = 6
        while retries:
            message = self._pop_email_for_client_once(email_address, content_filter=content_filter)
            if message:
                return message
            else:
                retries -= 1
                if retries == 0:
                    if fail_if_none:
                        self.fail('Email not received')
                time.sleep(5)


    def _pop_email_for_client_once(self, email_address, content_filter=None):
        from imapclient import IMAPClient
        message = None
        messages_to_delete = []
        server = IMAPClient(IMAP_HOST, ssl=True)
        for m_id, parsed_headers, body_text in self.all_emails(server):
            if email_address in parsed_headers['To']:
                body_text = body_text.replace('\r', '')
                body_text = body_text.replace('=\n', '')
                if content_filter is None or content_filter in body_text:
                    message = (
                        parsed_headers['From'],
                        parsed_headers['To'],
                        parsed_headers['Subject'],
                        body_text
                    )
                    messages_to_delete.append(m_id)
        server.delete_messages(messages_to_delete)
        return message


    def clear_email_for_address(self, email_address, content_filter=None):
        from imapclient import IMAPClient
        server = IMAPClient(IMAP_HOST, ssl=True)
        messages_to_delete = []
        for m_id, parsed_headers, body_text in self.all_emails(server):
            if email_address in parsed_headers['To']:
                if content_filter is None or content_filter in body_text:
                    messages_to_delete.append(m_id)
        server.delete_messages(messages_to_delete)


    def all_emails(self, server):
        server.login(IMAP_USERNAME, IMAP_PASSWORD)
        server.select_folder('INBOX')
        messages = server.search(['NOT DELETED'])
        response = server.fetch(messages, ['RFC822.TEXT', 'RFC822.HEADER'])
        parser = Parser()
        for m_id, m in response.items():
            parsed_headers = parser.parsestr(m['RFC822.HEADER'])
            body_text = m['RFC822.TEXT']
            yield (m_id, parsed_headers, body_text)

