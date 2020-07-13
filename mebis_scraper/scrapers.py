from selenium.common.exceptions import NoSuchElementException
from .exceptions import (UnsupportedActivityException,
                         UncompletableActivityException)
from contextlib import contextmanager
import logging


class LernplattformScraper:
    lernplattform_url = 'https://lernplattform.mebis.bayern.de'

    class Activity:
        def __init__(self, webelement):
            self.el = webelement

        def from_id(driver, el_id):
            return LernplattformScraper.Activity(
                driver.find_element_by_id(el_id))

        def from_element(webelement):
            return LernplattformScraper.Activity(webelement)

        def get_type(self):
            classes = self.el.get_attribute('class').split(' ')

            for class_name in classes:
                if class_name.startswith('modtype_'):
                    return class_name

            return None

        def get_download_link(self):
            return self.el.find_element_by_xpath(
                './/span[contains(@class, "instancename")]/..')

        def get_name(self):
            try:
                return self.el.find_element_by_css_selector(
                    'span.instancename').text.split('\n', maxsplit=1)[0]
            except NoSuchElementException:
                try:
                    return self.el.find_element_by_css_selector(
                        'span.fp-filename'
                    ).text.split('\n', maxsplit=1)[0]
                except NoSuchElementException:
                    if self.get_type() == 'modtype_label':
                        return (self.get_label_element().text
                                .split('\n', maxsplit=1)[0])
                    return ''

        def get_subtext(self):
            try:
                return self.el.find_element_by_class_name(
                    'contentafterlink').get_attribute('outerHTML')
            except NoSuchElementException:
                return None

        def get_complete_button_element(self):
            try:
                return self.el.find_element_by_css_selector(
                    'button.btn.btn-link')
            except NoSuchElementException:
                raise UncompletableActivityException

        def get_complete_button_state(self):
            btn = self.get_complete_button_element()

            img = btn.find_element_by_tag_name('img')
            alt = img.get_attribute('alt')
            return alt.startswith('Abgeschlossen')

        def get_complete_button_state_none(self):
            try:
                return self.get_complete_button_state()
            except UncompletableActivityException:
                return None

        def get_complete_button_state_false(self):
            try:
                return self.get_complete_button_state()
            except UncompletableActivityException:
                return False

        def toggle_complete_button(self):
            self.get_complete_button_element().click()

        def set_complete_button_state(self, state):
            if state != self.get_complete_button_state():
                self.toggle_complete_button()

        # all Activity instances _may_ be invalidated after a call to this
        # function. Use IDs instead.
        def download(self, driver, auth):
            DOWNLOADERS = {
                'modtype_resource': self._download_resource,
                'modtype_folder': self._download_folder,
                'modtype_label': self._download_label,
                'modtype_page': self._download_page,
                'modtype_url': self._download_link
            }

            el_id = self.el.get_attribute('id')
            try:
                res = DOWNLOADERS[self.get_type()](driver, auth)
            except KeyError:
                raise UnsupportedActivityException(self.get_type())
            else:
                self.el = driver.find_element_by_id(el_id)
                return res

        def _download_resource(self, driver, auth):
            self.get_download_link().click()
            auth.handle_login_page(driver)

            return None

        def find_folder_download_button(el):
            return el.find_element_by_xpath(
                ".//input[@value='Verzeichnis herunterladen']")

        def download_folder(el):
            LernplattformScraper.Activity.find_folder_download_button(el) \
                                         .click()

        # may change page
        def _download_folder(self, driver, auth):
            try:
                self.__class__.download_folder(self.el)
                auth.handle_login_page(driver)
            except NoSuchElementException:
                old_page = driver.current_url

                self.get_download_link().click()
                auth.handle_login_page(driver)

                self.__class__.download_folder(driver)
                auth.handle_login_page(driver)

                driver.get(old_page)

            return None

        def _download_page(self, driver, auth):
            old_page = driver.current_url

            self.get_download_link().click()
            auth.handle_login_page(driver)

            res = driver.find_element_by_class_name('generalbox').get_attribute('outerHTML')

            driver.get(old_page)

            return res

        def _download_link(self, driver, auth):
            return self.get_download_link().get_attribute('href')

        def get_label_element(self):
            return self.el.find_element_by_class_name('contentwithoutlink')

        def _download_label(self, driver, auth):
            return self.get_label_element().get_attribute('outerHTML')

    class Subject:
        def __init__(self, webelement):
            self.el = webelement

        def from_element(webelement):
            return LernplattformScraper.Subject(webelement)

        def from_id(driver, id):
            return LernplattformScraper.Subject(driver.find_element_by_id(id))

        def get_activity_elements(self):
            # expand subject
            toggle_buttons = self.el.find_elements_by_css_selector(
                'span.toggle_closed')
            for button in toggle_buttons:
                button.click()

            return self.el.find_elements_by_css_selector('li.activity')

        def get_activities(self):
            activity_els = self.get_activity_elements()

            activities = map(LernplattformScraper.Activity.from_element,
                             activity_els)

            return list(activities)

        def get_activity_ids(self):
            activity_els = self.get_activity_elements()

            activities = map(lambda el: el.get_attribute('id'), activity_els)

            return list(activities)

        def get_name(self):
            try:
                return self.el.find_element_by_css_selector(
                    '.sectionname').text
            except NoSuchElementException:
                return ''

        def visit(self, visitor, auth, driver):
            activity_page = driver.current_url
            for activity_id in self.get_activity_ids():
                activity = LernplattformScraper.Activity.from_id(
                    driver, activity_id)

                visitor.accept_activity(activity, auth, driver)

                # The visitor might have executed a page change by downloading
                # the activity
                if driver.current_url != activity_page:
                    driver.get(activity_page)

    class Course:
        def __init__(self, driver):
            self.driver = driver

        def get_subject_elements(self):
            return self.driver.find_elements_by_css_selector('li.section.main')

        # assumes the current page has been acquired by the driver
        def get_subjects(self):
            return list(map(
                LernplattformScraper.Subject.from_element,
                self.get_subject_elements()))

        def get_subject_ids(self):
            return list(map(
                lambda el: el.get_attribute('id'),
                self.get_subject_elements()))

        def analyse_subcourse(el):
            link = el.find_element_by_css_selector('a')

            href = link.get_attribute('href')
            name = link.find_element_by_css_selector('span').text

            return (name, href)

        # finds all courses that are not yet selected
        def list_secondary_sub_courses(self):
            courses = self.driver.find_elements_by_xpath(
                '//ul[contains(@class, "nav-tabs")]/li[not(@class="active")]')

            scourses = map(self.analyse_subcourse.__func__, courses)

            return list(scourses)

        def get_current_subcourse_name(self):
            name = None

            try:
                current_course = self.driver.find_element_by_xpath(
                    '//ul[contains(@class, "nav-tabs")]/li[@class="active"]')

                name = current_course.find_element_by_css_selector('span').text
            except NoSuchElementException:
                pass  # name is already none

            return name

        def get_name(self):
            return self.driver.find_element_by_xpath(
                '//div[@class="course-headline"]').text

        def visit_subjects(self, visitor, auth):
            for subject_id in self.get_subject_ids():
                subject = LernplattformScraper.Subject.from_id(self.driver,
                                                               subject_id)
                name = subject.get_name()

                if visitor.enter_subject(name):
                    subject.visit(visitor, auth, self.driver)
                    visitor.exit_subject()

        def visit(self, visitor, auth):
            course_name = self.get_current_subcourse_name()

            if course_name is not None:
                if visitor.enter_subcourse(course_name):
                    self.visit_subjects(visitor, auth)
                    visitor.exit_subcourse()

                for subcourse in self.list_secondary_sub_courses():
                    (name, href) = subcourse

                    if visitor.enter_subcourse(name):
                        auth.acquire_page(self.driver, href)
                        self.visit_subjects(visitor, auth)

                        visitor.exit_subcourse()
            else:
                self.visit_subjects(visitor, auth)

    class Visitor:
        """Check whether the course with the specified name is to be entered
        """
        def enter_course(self, name):
            return True

        def exit_course(self):
            pass

        def enter_subcourse(self, name):
            return True

        def exit_subcourse(self):
            pass

        def enter_subject(self, name):
            pass

        def exit_subject(self):
            pass

        def accept_activity(self, activity, auth, driver):
            pass

    def __init__(self, driver, auth):
        self.auth = auth
        self.driver = driver

    @contextmanager
    def create(driver, auth):
        scraper = LernplattformScraper(driver, auth)

        try:
            yield scraper
        finally:
            scraper.logout()

    def _acquire_page(self, page):
        self.driver.get(page)
        self.auth.handle_login_page(self.driver)

    def debug_dump_page(self):
        with open('debug.html', 'w') as f:
            f.write(self.driver.page_source())

    def get_page_source(self):
        return self.driver.page_source()

    def logout(self):
        self._acquire_page(self.lernplattform_url)

        # span inside a logout link
        try:
            self.driver.find_element_by_xpath(
                "//span[text() = 'Logout']/..").click()
        except NoSuchElementException:
            logging.getLogger('LernplattformScraper') \
                   .warning('Logout failed')
            return False

        return True

    def scrape_courses(self):
        self._acquire_page(self.lernplattform_url)

        course_link_map = {}

        courses = self.driver.find_elements_by_class_name('coursename')
        for course in courses:
            link_tag = course.find_element_by_xpath('..')

            course_name = course.text
            course_link = link_tag.get_attribute('href')

            course_link_map[course_name] = course_link

        return course_link_map

    def visit(self, visitor):
        courses = self.scrape_courses()
        course_handler = LernplattformScraper.Course(self.driver)

        for course in courses.items():
            (name, href) = course

            if visitor.enter_course(name):
                self._acquire_page(href)
                course_handler.visit(visitor, self.auth)

                visitor.exit_course()
