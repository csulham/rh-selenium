import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
from .base_test import BaseTest, setup_driver, setup_browsermob  # Import the fixtures

class TestPhoneClick(BaseTest):
    URL = "https://aem-qs4.np.roberthalf.com/us/en/c/hire?internal_user=qaselenium&urm_campaign=qaTest"
    
    def setup_method(self, method):
        super().setup_method(method)
        self.test_name = "test_phone_click"
        self.test_id = 1
        
        # Metadata for domo
        test_suite = 'MSJO US-en'
        test_suite_version = '1.0.0'
        test_case_name = self.test_name
        test_case_version = '1.0.0'
        self.metadata_string = self.get_metadata_string(
            test_suite, test_suite_version, test_case_name, test_case_version
        )

@pytest.mark.parametrize("test_url", [TestPhoneClick.URL])
def test_hire_now_form(setup_driver, test_url):
    test_instance = TestPhoneClick()
    test_instance.setup_method(None)  # Initialize the test instance
    driver, proxy = setup_driver

    try:
        #load the page
        test_instance.log_info(f"{test_instance.metadata_string}|Navigating to {test_url}")        
        driver.get(test_url)
        test_instance.load_dataLayer_and_dismiss_cookie(driver)

        # Test the title and presence of specific text
        test_instance.log_assert("Page contains 'Hire Now' in title", "Hire Now" in driver.title, "Page title does not contain 'Hire Now'")

        # Navigate the shadow DOM to find the phone button
        form_root = driver.find_element(By.TAG_NAME, "rhcl-block-hero-form")
        test_instance.log_assert("Form element <rhcl-block-hero-form> detected", form_root is not None, "Form root not found")
        
        form_shadow_root = form_root.shadow_root
        test_instance.log_assert("Shadow root detected", form_shadow_root is not None, "Shadow root not found")

        phone_button = form_shadow_root.find_element(By.CSS_SELECTOR, "rhcl-button[component-title='1.855.432.0924']")
        test_instance.log_assert("Phone button detected", phone_button is not None, "Phone button not found")

        # Navigate the phone button shadow dom and click the phone button
        phone_button_shadow_root = phone_button.shadow_root
        test_instance.log_assert("Phone button shadow root detected", phone_button_shadow_root is not None, "Phone button shadow root not found")
        phone_link = phone_button_shadow_root.find_element(By.CSS_SELECTOR, "a[href='tel:1.855.432.0924']")
        test_instance.log_assert("Phone link detected", phone_link is not None, "Phone link not found") 
        phone_link.click()
        test_instance.log_info(f"{test_instance.metadata_string}| Phone link clicked")
        time.sleep(1)  # Wait for the click action to complete

        # Validate the phone number click event was added to the dataLayer
        test_instance.log_info(f"{test_instance.metadata_string}|'Validating dataLayer event'|{test_url}|Validating dataLayer event")
        data_layer = test_instance.get_data_layer(driver)
        expected_properties = {
            "page_topic": "lead form page",
            "page_user_type": "client",
            "page_zone": "7i2dtn",
            "event_text": "phone number"
        }
        test_instance.validate_datalayer_event(data_layer, "phone_click", expected_properties)

        # Validate GA4 collect request
        expected_properties = {
            "ep.page_topic": "lead form page",
            "ep.page_user_type": "client",
            "ep.page_zone": "7i2dtn",
            "ep.event_text": "phone number"
        }
        test_instance.validate_ga4_collect_event(proxy, "phone_click", expected_properties)

    except AssertionError as e:
        test_instance.test_result = "fail"
        test_instance.test_error_description = str(e)
        test_instance.log_error(f"{test_instance.metadata_string}|'Test failed'|{test_url}|{str(e)}")
        raise
    except Exception as e:
        test_instance.test_result = "fail"
        test_instance.test_error_description = str(e)
        test_instance.log_error(f"{test_instance.metadata_string}|'Unexpected error'|{test_url}|{str(e)}")
        raise
    finally:
        test_instance.test_finish_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # Comment out the file upload for now since it's not working
        # test_instance.upload_logs_to_gcs(test_instance.logs_file_name)

if __name__ == "__main__":
    pytest.main()