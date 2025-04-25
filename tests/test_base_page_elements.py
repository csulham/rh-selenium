import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import datetime
from .base_test import BaseTest, setup_driver, setup_browsermob  # Import the fixtures

class TestWithAsserts(BaseTest):
    URL = "https://aem-qs4.np.roberthalf.com/us/en/c/hire?internal_user=qaselenium&urm_campaign=qaTest"
    
    def setup_method(self, method):
        super().setup_method(method)
        self.test_name = "test_base_page_elements"
        self.test_id = 1
        
        # Metadata for domo
        test_suite = 'MSJO US-en'
        test_suite_version = '1.0.0'
        test_case_name = self.test_name
        test_case_version = '1.0.0'
        self.metadata_string = self.get_metadata_string(
            test_suite, test_suite_version, test_case_name, test_case_version
        )

@pytest.mark.parametrize("test_url", [TestWithAsserts.URL])
def test_hire_now_form(setup_driver, test_url):
    test_instance = TestWithAsserts()
    test_instance.setup_method(None)  # Initialize the test instance
    driver, proxy = setup_driver

    try:
        test_instance.log_info(f"{test_instance.metadata_string}|'Navigate to URL'|{test_url}|Navigating to {test_url}")
        driver.get(test_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "rhcl-dropdown"))
        )
        test_instance.log_info(f"{test_instance.metadata_string}|'Form Loaded'|{test_url}|Form elements detected")

        test_instance.log_assert("Page contains 'Hire Now' in title", "Hire Now" in driver.title, "Page title does not contain 'Hire Now'")
        #test_instance.log_assert("Page contains 'THIS TEST MUST FAIL' text", "THIS TEST MUST FAIL" in driver.page_source, "Page does not contain 'THIS TEST MUST FAIL' text")

        element = driver.find_element(By.ID, "container-9ad031068e")
        test_instance.log_assert("Element with ID 'container-9ad031068e' on page", element is not None, "Element with ID 'container-9ad031068e' not found")

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