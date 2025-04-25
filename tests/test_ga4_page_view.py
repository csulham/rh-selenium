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

    def validate_page_view_event(self, data_layer):
        self.log_info("Validating GA4 page_view event...")
        if not data_layer:
            assert False, "DataLayer is empty"
            
        for entry in data_layer:
            if isinstance(entry, list) and entry[0] == "event" and entry[1] == "page_view":
                data = entry[2]
                expected = {
                    "page_topic": "lead form page",
                    "page_section": "performance landing pages",
                    "page_user_type": "client",
                    "page_zone": "7i2dtn"
                }
                passed = True
                for k, v in expected.items():
                    self.log_assert(f"Checking dataLayer for {k}", k in data, f"Key '{k}' not found in dataLayer")
                    self.log_assert(f"Checking dataLayer for {k}=={v}", data[k] == v, f"Value for '{k}' does not match expected value. Expected: {v}, Found: {data[k]}")

                # Check user IDs
                self.log_assert("Checking user_id_ga", data.get('user_id_ga') is not None, "user_id_ga not found in dataLayer.")
                self.log_assert("Checking user_id_tealium", data.get('user_id_tealium') is not None, "user_id_tealium not found in dataLayer.")
                
                return passed
        
        assert False, "GA4 page_view event not found in dataLayer"

@pytest.mark.parametrize("test_url", [TestFormGA4.URL])
def test_hire_now_form(setup_driver, test_url):
    test_instance = TestFormGA4()
    test_instance.setup_method(None)  # Initialize the test instance
    driver, proxy = setup_driver

    try:
        test_instance.log_info(f"{test_instance.metadata_string}|'Navigate to URL'|{test_url}|Navigating to {test_url}")
        #load the page
        driver.get(test_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "rhcl-dropdown"))
        )

        #refresh the page to ensure all dataLayer events are loaded. user_id_ga is set on second visit.
        driver.refresh()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "rhcl-dropdown"))
        )
        test_instance.log_info(f"{test_instance.metadata_string}|'Form Loaded'|{test_url}|Form elements detected")

        # Test the title and presence of specific text
        test_instance.log_assert("Page contains 'Hire Now' in title", "Hire Now" in driver.title, "Page title does not contain 'Hire Now'", test_url)
        
        data_layer = test_instance.get_data_layer(driver)
        test_instance.validate_page_view_event(data_layer)

        # API Request Assertion
        max_retries = 3

        har_dict = proxy.har
        target_url = "https://www.google-analytics.com/g/collect"
        request_found = False
        actual_request_url = None
        all_requests = []

        for attempt in range(max_retries):
            test_instance.log_info(f"Checking HAR logs (Attempt {attempt+1}/{max_retries})...")

            har_dict = proxy.har  # Get the latest network logs

            for entry in har_dict['log']['entries']:
                request = entry['request']
                all_requests.append(request['url'])

                if target_url in request['url'] and "en=page_view" in request['url']:
                    actual_request_url = request['url']
                    test_instance.log_info(f"Request sent to: {actual_request_url}")
                    request_found = True
                    break

            if request_found:
                break  # Exit loop if request is found
            time.sleep(5)  # Wait before retrying

        test_instance.log_assert(F"GA4 request found in HAR logs: {actual_request_url}", request_found, f"'GA4 collect confirmation: no request found to {target_url}")


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