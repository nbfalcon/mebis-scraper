class AuthenticationManager:
    def __init__(self, authl):
        self.authl = authl

    def __init__(self):
        self.authl = []

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
