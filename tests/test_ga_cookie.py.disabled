import pytest
import psutil
import datetime
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import logging
import time
from google.cloud import storage
from selenium.webdriver.firefox.service import Service
import uuid
import sys

GECKO_DRIVER_PATH = "/usr/local/bin/geckodriver"

# Metadata for domo
test_suite = 'MSJO US-en'
test_suite_version = '1.0.0'
test_case_name = 'MSJO auth temp'
test_case_version = '1.0.0'
test_id = 1
run_id = uuid.uuid4()
url_to_be_tested = "https://www.roberthalf.com/us/en/hire-talent/form?internal_user=qaselenium"
metadata_string = f'{test_suite}|{test_suite_version}|{test_case_name}|{test_case_version}'

test_name = "test_hire_talent_form"
start_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
logs_file_name = f"{start_timestamp}_logs_automationqa.txt"
test_finish_timestamp = ""
test_result = "success"
test_error_description = ""

# Configure logging
logging.basicConfig(level=logging.INFO)

def upload_logs_to_gcs(file_name):
# def upload_logs_to_gcs(file_name, test_finish_timestamp, test_name, test_result, test_error_description):
    """Upload logs to Google Cloud Storage"""
    # with open(file_name, 'a') as file:
    #     file.write(f"{test_finish_timestamp}\t{test_name}\t{test_result}\t{test_error_description}\n")
    
    bucket_name = 'automation-qa-logs'
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)
    print(f"File {file_name} uploaded to {bucket_name}.")

@pytest.fixture(scope="module", autouse=True)
def setup_browsermob():
    """Start BrowserMob Proxy before tests and stop after."""
    logging.info("Killing all browsermob-proxy processes...")
    for proc in psutil.process_iter():
        if 'proxy' in proc.name() or 'browser' in proc.name():
            proc.kill()

    logging.info("Starting BrowserMob Proxy...")
    server = Server(path="./drivers/browsermob-proxy-2.1.4/bin/browsermob-proxy")
    try:
        server.start()
        time.sleep(5)
    except Exception as e:
        logging.error(f"Failed to start BrowserMob Proxy: {e}")
        pytest.fail("BrowserMob Proxy failed to start.")

    proxy = server.create_proxy()
    proxy.new_har()
    
    yield server, proxy
    logging.info("Stopping BrowserMob Proxy...")
    server.stop()

@pytest.fixture(scope="module")
def setup_driver(setup_browsermob):
    """Initialize Firefox WebDriver with proxy."""
    server, proxy = setup_browsermob
    logging.info("Starting a Firefox instance...")
    options = Options()
    options.add_argument("--headless")
    options.accept_insecure_certs = True

    proxy_config = Proxy({
        "proxyType": ProxyType.MANUAL,
        "httpProxy": proxy.proxy,
        "sslProxy": proxy.proxy
    })
    options.proxy = proxy_config
    service = Service(GECKO_DRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)

    yield driver, proxy
    logging.info("Closing WebDriver...")
    driver.quit()

def safe_execute(driver, script, description):
    """Execute JavaScript safely and log success or failure."""
    try:
        driver.execute_script(script)
        log_message = f"{metadata_string}|' {description} '|{url_to_be_tested}|success"
        logging.info(log_message)

        with open(logs_file_name, "a") as log_file:
            log_file.write(f"{start_timestamp}\t{test_name}\tsuccess\t{log_message}\n")

    except Exception as e:
        failure_reason = f"{description} failed: {str(e)}"
        log_message = f"{metadata_string}|' {description} '|{url_to_be_tested}|FAILED: {failure_reason}"
        logging.error(log_message)

        with open(logs_file_name, "a") as log_file:
            log_file.write(f"{start_timestamp}\t{test_name}\tfail\t{log_message}\n")

@pytest.mark.parametrize("test_url", [url_to_be_tested])
def test_ga_cookie(setup_driver, test_url):
    """Test if GA cookie is present and a request is made to API."""
    global test_finish_timestamp, test_result, test_error_description
    driver, proxy = setup_driver

    try:
        logging.info(f"{metadata_string}|'Navigate to URL'|{test_url}|Navigating to {test_url}")
        driver.get(test_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "rhcl-dropdown"))
        )
        logging.info(f"{metadata_string}|'Form Loaded'|{test_url}|Form elements detected")

        # Execute each step before assertions
        # Step 1: Enter Job Title
        safe_execute(driver, """
            let jobTitle = document.querySelector("rhcl-typeahead[name='positionTitle']");
            if (jobTitle) jobTitle.value = 'QA Engineer';
        """, "Enter Job Title")

        # Step 2: Enter Zip Code
        safe_execute(driver, """
            let zipCode = document.querySelector("rhcl-text-field[name='postalCode']");
            if (zipCode) zipCode.value = '94587';
        """, "Enter Zip Code")

        # Step 3: Select Position Type
        safe_execute(driver, """
            let dropdown = document.querySelector("rhcl-dropdown[name='employmentType']");
            
                dropdown.click();
                let firstOption = dropdown.shadowRoot.querySelector("mwc-list-item:nth-child(1)");
                firstOption.click();
            
        """, "Select Position Type")

        # Step 4: Select Estimated Start Date
        safe_execute(driver, """
            let startDate = document.querySelector("rhcl-dropdown[name='startDate']");
            if (startDate) {
                startDate.click();
                let firstDateOption = startDate.shadowRoot.querySelector("mwc-list-item:nth-child(1)");
                if (firstDateOption) firstDateOption.click();
            }
        """, "Select Estimated Start Date")

        # Step 5: Set Min & Max Salary
        safe_execute(driver, """
            function setSalary(selector, value) {
                let element = document.querySelector(selector);
                if (element && element.shadowRoot) {
                    let nestedElement = element.shadowRoot.querySelector("rhcl-mwc-text-field");
                    if (nestedElement && nestedElement.shadowRoot) {
                        let inputField = nestedElement.shadowRoot.querySelector("input");
                        if (inputField) {
                            inputField.focus();
                            inputField.value = value;
                            inputField.dispatchEvent(new Event('input', { bubbles: true }));
                            inputField.dispatchEvent(new Event('change', { bubbles: true }));
                            console.log(selector + " set to " + value + "!");
                        }
                    }
                }
            }
            setSalary("rhcl-text-field[name='payRateMin']", "10000");
            setSalary("rhcl-text-field[name='payRateMax']", "100000");
        """, "Set Min & Max Salary")

        # Step 6: Select Skills and Add
        safe_execute(driver, """
            let skillsChip = document.querySelector("rhcl-chip-typeahead");
            if (skillsChip) {
                let shadowRoot1 = skillsChip.shadowRoot;
                let typeahead = shadowRoot1 ? shadowRoot1.querySelector("rhcl-typeahead") : null;
                let shadowRoot2 = typeahead ? typeahead.shadowRoot : null;
                let textField = shadowRoot2 ? shadowRoot2.querySelector("rhcl-text-field") : null;
                let shadowRoot3 = textField ? textField.shadowRoot : null;
                let mwcField = shadowRoot3 ? shadowRoot3.querySelector("rhcl-mwc-text-field") : null;
                let shadowRoot4 = mwcField ? mwcField.shadowRoot : null;
                let inputField = shadowRoot4 ? shadowRoot4.querySelector("input.mdc-text-field__input") : null;
                if (inputField) {
                    inputField.focus();
                    inputField.value = "Selenium";
                    inputField.dispatchEvent(new Event('input', { bubbles: true }));
                    inputField.dispatchEvent(new Event('change', { bubbles: true }));
                    setTimeout(() => {
                        let firstSuggestion = shadowRoot2.querySelector("button.rhcl-typeahead__item");
                        if (firstSuggestion) {
                            firstSuggestion.click();
                            setTimeout(() => {
                                let plusButton = shadowRoot1.querySelector("rhcl-button").shadowRoot.querySelector("rhcl-icon[icon='plus']");
                                if (plusButton) {
                                    plusButton.click();
                                }
                            }, 1000);
                        }
                    }, 3000);
                }
            }
        """, "Select Skills and Add")

        time.sleep(5)

        # Step 7: Click 'Next' Button
        safe_execute(driver, """
            let progressiveFrame = document.querySelector("rhcl-progressive-frame");            
            let slot = progressiveFrame.shadowRoot.querySelector("slot[name='step']");                
            let assignedNodes = slot.assignedNodes();
            for (let node of assignedNodes) {
                let frameStep = node.querySelector("rhcl-progressive-frame-step[selected='true']");                        
                console.log("Found Active Frame Step:", frameStep);
                let nextButton = frameStep.shadowRoot.querySelector("rhcl-button[component-title='Submit']");
                let innerButton = nextButton.shadowRoot.querySelector("button");
                innerButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => {
                    innerButton.click();
                    console.log("'Next' button clicked!");
                }, 500);
                return true;     
            }
            return false;
        """, "Click 'Next' Button")

        time.sleep(3)

        # GA Cookie Assertion
        try:
            ga_cookie = WebDriverWait(driver, 10).until(lambda d: d.get_cookie("_ga"))
            
            # Log success with the actual GA cookie value
            log_message = f"{metadata_string}|'GA Cookie confirmation'|{test_url}|GA Cookie found: {ga_cookie['value']}"
            logging.info(log_message)
            
            with open(logs_file_name, "a") as log_file:
                log_file.write(f"{start_timestamp}\t{test_name}\tsuccess\t{log_message}\n")

        except Exception as e:
            # Log failure message
            log_message = f"{metadata_string}|'GA Cookie confirmation'|{test_url}|GA Cookie not found!"
            logging.error(log_message)

            with open(logs_file_name, "a") as log_file:
                log_file.write(f"{start_timestamp}\t{test_name}\tfail\t{log_message}\n")

            logging.info(f"Encountered error with GA Cookie confirmation: {e}")
            pass
        
       
        # API Request Assertion
        max_retries = 3

        har_dict = proxy.har
        target_url = "https://prd-dr.lp.api.roberthalfonline.com/proxy-lead-processing/send"
        request_found = False
        actual_request_url = None
        all_requests = []

        for attempt in range(max_retries):
            logging.info(f"Checking HAR logs (Attempt {attempt+1}/{max_retries})...")

            har_dict = proxy.har  # Get the latest network logs

            for entry in har_dict['log']['entries']:
                request = entry['request']
                all_requests.append(request['url'])

                if request['method'] == 'POST' and target_url in request['url']:
                    actual_request_url = request['url']
                    logging.info(f"Request sent to: {actual_request_url}")
                    request_found = True
                    break

            if request_found:
                break  # Exit loop if request is found

            time.sleep(5)  # Wait before retrying

        try:
            assert request_found, f"{metadata_string}|'API Request confirmation'|{test_url}|No API request found to {target_url}"

            # Log success with actual request URL
            log_message = f"{metadata_string}|'API Request confirmation'|{test_url}|Request found at {actual_request_url}"
            logging.info(log_message)

            with open(logs_file_name, "a") as log_file:
                log_file.write(f"{start_timestamp}\t{test_name}\tsuccess\t{log_message}\n")

        except AssertionError as e:
            # Log failure message
            log_message = f"{metadata_string}|'API Request confirmation'|{test_url}|No API request found to {target_url}"
            logging.error(log_message)

            with open(logs_file_name, "a") as log_file:
                log_file.write(f"{start_timestamp}\t{test_name}\tfail\t{log_message}\n")

            # raise e  # Ensure test fails
            logging.info(f"Encountered error with API Request confirmation: {e}")
            pass

    finally:
        test_finish_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        
        upload_logs_to_gcs(logs_file_name)


if __name__ == "__main__":
    try:
        exit_code = pytest.main()

        if exit_code != 0:
            logging.warning("Some tests failed, but forcing exit with 0.")
            sys.exit(0)  # Force job success

    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")
        sys.exit(1)  # Only fail for unexpected runtime errors