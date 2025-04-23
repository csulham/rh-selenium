from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from pages.base_page import BasePage

class FormPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        # # Locators
        # self.name_input = (By.ID, "name")
        # self.email_input = (By.ID, "email")
        # self.select_option = (By.ID, "options")
        # self.submit_button = (By.ID, "submit")
        # self.success_message = (By.ID, "success")
        self.driver = driver
        self.search_text_box_locator = (By.ID, "id-search-field")
        self.submit_button_locator = (By.ID, "submit")

        #serch_text_box_element = self.find_element(self.search_text_box_locator)
    # def set_text_to_search(self, text_to_search):
    #     self.search_element = self.driver.find_element(*self.search_locator)
    #     self.search_element.send_keys(text_to_search)
    def set_text_to_search(self, text_to_search):
        self.fill_input(self.search_text_box_locator, text_to_search)
        
    def submit(self):
        self.click(self.submit_button_locator)
        if "No results found." not in self.driver.page_source:
            return "found"
        else:
            return "not found"
        #self.search_element.send_keys(Keys.RETURN)
        # if "No results found." not in self.driver.page_source:
        #     return "found"
        # else:
        #     return "not found"
        
    # def set_name(self, name):
    #     self.driver.find_element(*self.name_input).send_keys(name)

    # def set_email(self, email):
    #     self.driver.find_element(*self.email_input).send_keys(email)

    # def select_option_by_value(self, value):
    #     select = Select(self.driver.find_element(*self.select_option))
    #     select.select_by_value(value)
    
    # def submit_form(self):
    #     self.driver.find_element(*self.submit_button).click()

    # def get_success_message(self):
    #     return self.driver.find_element(*self.success_message).text
