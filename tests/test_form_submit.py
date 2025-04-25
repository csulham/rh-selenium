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
        self.test_name = "test_form_submit"
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

        test_instance.log_info(f"{test_instance.metadata_string}|'Form Loaded'|{test_url}|Form elements detected")

        #dismiss cookie banner if present
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
            test_instance.log_info("Cookie banner dismissed")
        except:
            test_instance.log_info("No cookie banner")

        # Test the title and presence of specific text
        test_instance.log_assert("Page contains 'Hire Now' in title", "Hire Now" in driver.title, "Page title does not contain 'Hire Now'", test_url)
        
        # Fill out the form fields
        form_fields = [
            ("rhcl-typeahead[name='positionTitle']", "Quality Assurance Engineer", "Job Title"),
            ("rhcl-text-field[name='postalCode']", "99502", "Zip Code"),
            ("rhcl-textarea[name='additionalInfo']", "Test message", "Comments"),
            ("rhcl-text-field[name='firstName']", "Jes", "First Name"),
            ("rhcl-text-field[name='lastName']", "Carney", "Last Name"),
            ("rhcl-text-field[name='phoneNumber']", "1234567890", "Phone Number"),
            ("rhcl-text-field[name='email']", "jes@example.com", "Email"),
            ("rhcl-text-field[name='companyName']", "Robert Half", "Company Name"),
            ("rhcl-text-field[name='customerTitle']", "Director", "Customer Title")
        ]

        for selector, value, label in form_fields:
            test_instance.fill_field(driver, selector, value, label)

        # Dropdown and checkbox
        try:
            driver.execute_script("""
                const el = document.querySelector("rhcl-dropdown[name='employmentType']");
                el.interactionRef.value = "Contract Talent";
                el.interactionRef.dispatchEvent(new Event('change', { bubbles: true }));
            """)
            # Assert that the field was filled with the correct value
            filled_value = driver.execute_script("""return document.querySelector("rhcl-dropdown[name='employmentType']").interactionRef.value;""")
            test_instance.log_assert("Employment Type dropdown field filled correctly", filled_value == "Contract Talent", f"Expected 'Contract Talent', but got {filled_value}", test_url)
        except Exception as e:
            test_instance.log_error(f"Could not set Employment Type dropdown: {e}")

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