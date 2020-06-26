from selenium.common.exceptions import NoSuchElementException

class LernplattformScraper:
    lernplattform_url = 'https://lernplattform.mebis.bayern.de'

    class NamedResource:
        def __init__(self, name, url):
            self.name = name
            self.url = url

    class Activity(NamedResource):
        def __init__(self, name, url, rtype):
            super().__init__(name, url)
            self.rtype = rtype

    def __init__(self, driver, auth):
        self.auth = auth
        self.driver = driver

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
        self.driver.find_element_by_xpath("//span[text() = 'Logout']/..").click()

    def scrape_courses(self):
        self._acquire_page(self.lernplattform_url)

        course_link_map = {}

        courses = self.driver.find_elements_by_class_name('coursename')
        for course in courses:
            link_tag = course.find_element_by_xpath('..')

            course_name = course.text
            course_link = link_tag.get_attribute('href')

            # TODO: HACK: Make configurable
            if course_name != 'Klasse 9 m':
                continue

            course_link_map[course_name] = course_link

        return course_link_map

    def scrape_course(self, link):
        self._acquire_page(link)

        # .span12 to skip general
        subjects = self.driver.find_elements_by_css_selector('li.section')
        subjects_res = {}
        for subject in subjects:
            # expand subject
            toggle_buttons = subject.find_elements_by_css_selector('span.toggle_closed')
            for button in toggle_buttons:
                button.click()

            # get activities
            activities = subject.find_elements_by_css_selector('span.instancename')
            activities_res = {}
            for activity in activities:
                name = activity.text.split('\n', maxsplit=1)[0]
                link = activity.find_element_by_xpath('..').get_attribute('href')

                activities_res[name] = link

            name = None
            try:
                name = subject.find_element_by_css_selector('.sectionname').text
            # except general section
            except NoSuchElementException:
                name = ''

            subjects_res[name] = activities_res

        return subjects_res

    # for this to work, the webdriver must be configured to _automatically_ save downloads
    def download_activity(self, activity_href):
        old_url = self.driver.current_url

        self._acquire_page(activity_href)

        # if the URL would not have changed, then a file would have been
        # downloaded; otherwise it is some kind of webpage that must be scraped
        if (self.driver.current_url != old_url):
            pass # TODO: implement
        else:
            pass # TODO: return file somehow

    def scrape_all(self):
        res = {}

        courses = self.scrape_courses()

        for course in courses.items():
            (course_name, course_link) = course
            course_subjects = self.scrape_course(course_link)

            res[course_name] = course_subjects

        return res
