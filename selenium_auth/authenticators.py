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
