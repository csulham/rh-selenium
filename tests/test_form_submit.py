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

    def collect_hidden_inputs(self, driver):
        """
        Collect and log all hidden input fields on the page using Selenium.
        """
        try:
            self.log_info("Collecting hidden input fields...")
            
            # Find all input elements
            hidden_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="hidden"]')
            
            if hidden_inputs:
                self.log_info(f"Found {len(hidden_inputs)} hidden input fields:")
                result = []
                for input_field in hidden_inputs:
                    input_data = {
                        'name': input_field.get_attribute('name') or '',
                        'id': input_field.get_attribute('id') or '',
                        'value': input_field.get_attribute('value') or '',
                        'type': input_field.get_attribute('type') or ''
                    }
                    result.append(input_data)
                    self.log_info(f"Hidden Input - Name: {input_data['name']}, "
                                f"ID: {input_data['id']}, "
                                f"Type: {input_data['type']}, "
                                f"Value: {input_data['value']}")
                return result
            else:
                self.log_info("No hidden input fields found on the page")
                return []
                
        except Exception as e:
            self.log_error(f"Error collecting hidden inputs: {e}")
            return []



    def fill_field(self, driver, selector, value, label):
        try:
            self.log_info(f"Typing {label}...")
            js_script = """
                const el = document.querySelector(arguments[0]);
                if (!el || !el.interactionRef) throw new Error(arguments[2] + ' interactionRef not found');
                const input = el.interactionRef;
                input.scrollIntoView();
                input.focus();
                input.value = arguments[1];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """
            driver.execute_script(js_script, selector, value, label)
            
            check_value_script = "return document.querySelector(arguments[0]).interactionRef.value;"
            filled_value = driver.execute_script(check_value_script, selector)

            self.log_assert(f"'{label}' field filled correctly", filled_value == value, f"Expected '{value}', but got '{filled_value}'")
        
        except Exception as e:
            self.log_error(f"Error filling field '{label}': {e}")

        

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
        
        # Navigate the shadow DOM 
        form_root = driver.find_element(By.TAG_NAME, "rhcl-block-hero-form")
        test_instance.log_assert("Form element <rhcl-block-hero-form> detected", form_root is not None, "Form root not found")
        
        form_shadow_root = form_root.shadow_root
        test_instance.log_assert("Shadow root detected", form_shadow_root is not None, "Shadow root not found")

        # Fill out the form fields
        form_fields = [
            ("rhcl-typeahead[name='positionTitle']", "Quality Assurance Engineer", "Job Title"),
            ("rhcl-text-field[name='postalCode']", "99502", "Zip Code"),
            ("rhcl-textarea[name='additionalInfo']", "Test message", "Comments"),
            ("rhcl-text-field[name='firstName']", "Jes", "First Name"),
            ("rhcl-text-field[name='lastName']", "Carney", "Last Name"),
            ("rhcl-text-field[name='phoneNumber']", "6174403840", "Phone Number"),
            ("rhcl-text-field[name='email']", "jes@example.com", "Email"),
            ("rhcl-text-field[name='companyName']", "Robert Half", "Company Name"),
            ("rhcl-text-field[name='customerTitle']", "Director", "Customer Title")
        ]

        for selector, value, label in form_fields:
            test_instance.fill_field(driver, selector, value, label)

        # Dropdown for Position Type        
        driver.execute_script("""
            const el = document.querySelector("rhcl-dropdown[name='employmentType']");
            if (!el || !el.interactionRef) throw new Error("Dropdown interactionRef not found");
            el.interactionRef.value = "temp";
            el.interactionRef.dispatchEvent(new Event('change', { bubbles: true }));
        """)
        check_value_script = """return document.querySelector("rhcl-dropdown[name='employmentType']").interactionRef.value;"""
        filled_value = driver.execute_script(check_value_script)

        test_instance.log_assert("Position Type drop down filled correctly?", filled_value == "temp", f"Expected 'temp', but got '{filled_value}'")

        # Remote checkbox
        driver.execute_script("""
                const checkbox = document.querySelector("rhcl-checkbox[name='remoteEligible']");
                if (!checkbox || !checkbox.interactionRef) throw new Error("Remote checkbox not found");
                checkbox.interactionRef.click();
            """)
        check_value_script = """return document.querySelector("rhcl-checkbox[name='remoteEligible']").interactionRef.checked;"""
        filled_value = driver.execute_script(check_value_script)
        test_instance.log_assert("Remote checkbox checked?", filled_value, "Checkbox not checked")

        # Get Submit button
        submit_button = driver.find_element(By.CSS_SELECTOR, "rhcl-button[component-title='Submit']")
        test_instance.log_assert("Submit button exists?", submit_button is not None, "Submit button not found")
        
        # Get the page form
        page_form = driver.find_element(By.TAG_NAME, "form")
        test_instance.log_assert("Form element <form> detected", page_form is not None, "Form element not found")

        # Validate the form action
        form_action = page_form.get_attribute("action")
        expected_form_action_url = "https://qs04-dr.int-qs-lp.api.roberthalfonline.com/proxy-lead-processing/send"
        test_instance.log_assert("Form action URL is correct", form_action == expected_form_action_url, f"Form action URL incorrect. Found: {form_action}")

        # Scroll the submit button into view
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        
        # Wait a bit for any animations to complete
        time.sleep(1)
        
        # Submit the form using JavaScript because clicking the button isn't firing the submit event
        submit_button.click()

        # Check for validation errors
        test_instance.log_info("Checking for validation errors...")
        validation_errors = driver.execute_script("""
            // Select all relevant form field elements
            const formFields = document.querySelectorAll('rhcl-text-field, rhcl-checkbox, rhcl-typeahead, rhcl-textarea, rhcl-dropdown');
            let errors = [];
            
            for (const field of formFields) {
                if (field.shadowRoot) {
                    const shadowErrors = field.shadowRoot.querySelectorAll('rhcl-form-field-error');
                    for (const error of shadowErrors) {
                        errors.push({
                            field: field.getAttribute('name'),
                            tagName: field.tagName.toLowerCase(),
                            outerHTML: error.outerHTML,
                            innerHTML: error.innerHTML,
                            textContent: error.textContent,
                            shadowContent: error.shadowRoot ? error.shadowRoot.innerHTML : null
                        });
                    }
                }
            }
            
            return errors;
        """)

        test_instance.log_info(f"Found {len(validation_errors)} validation errors")
        
        # Log detailed information about each validation error
        if validation_errors:
            for error in validation_errors:
                test_instance.log_info("Validation Error Details:")
                test_instance.log_info(f"Field: {error['field']}")
                test_instance.log_info(f"Full HTML: {error['outerHTML']}")
                test_instance.log_info(f"Inner HTML: {error['innerHTML']}")
                test_instance.log_info(f"Text Content: {error['textContent']}")
                test_instance.log_info(f"Shadow Content: {error['shadowContent']}")
                test_instance.log_info("---")
            
        test_instance.log_assert("No validation errors", len(validation_errors) == 0, "Validation errors found")

        # Wait for the form to be submitted and check for success message
        test_instance.log_info("Waiting for thank you message...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "rhcl-typography[id='thankYouCopy']"))
        )

        # Validate the success message
        success_message = driver.find_element(By.CSS_SELECTOR, "rhcl-typography[id='thankYouCopy']").text
        test_instance.log_assert("Success message displayed?", "Thank You" in success_message, f"Success message incorrect. Found: {success_message}")
        
        # Add wait for form submission processing
        time.sleep(15)

        test_instance.get_request_response_payload(proxy, expected_form_action_url)

        # Validate the dataLayer event
        data_layer = test_instance.get_data_layer(driver)
        expected_properties = {
            "form_type": "job-order",
            "event_action": "rhcl-button-clicked",
            "page_topic": "lead form page",
            "page_user_type": "client",
            "page_zone": "7i2dtn",
            "indicator_remote": "true",
            "job_title": "quality assurance engineer",
            "job_type": "temp",
            "location": "99502",
            "event_text": "submit"
        }
        test_instance.validate_datalayer_event(data_layer, "job_order_submit", expected_properties)

        # Validate GA4 collect request        
        expected_properties = {
            "ep.form_type": "job-order",
            "ep.event_action": "rhcl-button-clicked",
            "ep.page_topic": "lead form page",
            "ep.page_user_type": "client",
            "ep.page_zone": "7i2dtn",
            "ep.indicator_remote": "true",
            "ep.job_title": "quality assurance engineer",
            "ep.job_type": "temp",
            "ep.location": "99502",
            "ep.event_text": "submit"
        }
        test_instance.validate_ga4_collect_event(proxy, "job_order_submit", expected_properties)

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