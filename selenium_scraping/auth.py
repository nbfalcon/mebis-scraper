class AuthenticationManager:
    def __init__(self, authl=[]):
        self.authl = authl

    def acquire_page(self, driver, url):
        driver.get(url)
        self.handle_login_page(driver)

    def add_authenticator(self, auth):
        self.authl.append(auth)

    def is_login_page(self, driver):
        for auth in self.authl:
            if auth.is_login_page(driver):
                return True

        return False

    def handle_login_page(self, driver):
        for auth in self.authl:
            if auth.is_login_page(driver):
                auth.handle_login_page(driver)
                break


class MebisSAMLAuthenticator:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def is_login_page(self, driver):
        return driver.title == 'Mebis Login Service'

    def handle_login_page(self, driver):
        driver.find_element_by_id('username').send_keys(self.username)
        driver.find_element_by_id('password').send_keys(self.password)

        driver.find_element_by_id('submitbutton').click()
