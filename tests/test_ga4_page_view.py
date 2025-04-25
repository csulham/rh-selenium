import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import datetime
from .base_test import BaseTest, setup_driver, setup_browsermob  # Import the fixtures

class TestFormGA4(BaseTest):
    URL = "https://aem-qs4.np.roberthalf.com/us/en/c/hire?internal_user=qaselenium&urm_campaign=qaTest"
    
    def setup_method(self, method):
        super().setup_method(method)
        self.test_name = "test_ga4_page_view"
        self.test_id = 2
        
        # Metadata for domo
        test_suite = 'MSJO US-en'
        test_suite_version = '1.0.0'
        test_case_name = self.test_name
        test_case_version = '1.0.0'
        self.metadata_string = self.get_metadata_string(
            test_suite, test_suite_version, test_case_name, test_case_version
        )

@pytest.mark.parametrize("test_url", [TestFormGA4.URL])
def test_hire_now_form(setup_driver, test_url):
    test_instance = TestFormGA4()
    test_instance.setup_method(None)  # Initialize the test instance
    driver, proxy = setup_driver

    try:
        test_instance.log_info(f"{test_instance.metadata_string}|'Navigate to URL'|{test_url}|Navigating to {test_url}")
        #load the page
        driver.get(test_url)
        test_instance.load_dataLayer_and_dismiss_cookie(driver)
        test_instance.log_info(f"{test_instance.metadata_string}|'Form Loaded'|{test_url}|Form elements detected")

        # Test the title and presence of specific text
        test_instance.log_assert("Page contains 'Hire Now' in title", "Hire Now" in driver.title, "Page title does not contain 'Hire Now'")
        
        # Test the page view event in dataLayer
        data_layer = test_instance.get_data_layer(driver)
        expected_properties = {
            "page_topic": "lead form page",
            "page_section": "performance landing pages",
            "page_user_type": "client",
            "page_zone": "7i2dtn"
        }
        test_instance.validate_ga4_event(data_layer, "page_view", expected_properties)

        # Validate GA4 collect request
        test_instance.validate_ga4_collect_event(proxy, "page_view")

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