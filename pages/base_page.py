from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# import logging

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    # def open_url(self, url):
    #     self.driver.get(url)

    def find_element(self, locator):
        element = self.wait.until(EC.visibility_of_element_located(locator))
        return element

    def fill_input(self, locator, text):
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)

    def click(self, locator):
        self.find_element(locator).click()