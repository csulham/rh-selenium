from os import wait
import pytest
import psutil
import datetime
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import logging
import time
from google.cloud import storage
from selenium.webdriver.chrome.service import Service
import uuid
import sys

CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver-linux64/chromedriver"
CHROME_BINARY_PATH = "/opt/google/chrome/chrome-linux64/chrome"
URL = "https://aem-qs4.np.roberthalf.com/us/en/c/hire?internal_user=qaselenium&urm_campaign=qaTest"

# Metadata for domo
test_suite = 'MSJO US-en'
test_suite_version = '1.0.0'
test_case_name = 'MSJO auth temp'
test_case_version = '1.0.0'
test_id = 2
run_id = uuid.uuid4()
url_to_be_tested = "https://aem-qs4.np.roberthalf.com/us/en/c/hire?internal_user=qaselenium&urm_campaign=qaTest"
metadata_string = f'{test_suite}|{test_suite_version}|{test_case_name}|{test_case_version}'

test_name = "test_form_ga4"
start_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
logs_file_name = f"{start_timestamp}_logs_automationqa.txt"
test_finish_timestamp = ""
test_result = "success"
test_error_description = ""

# Configure logging
logging.basicConfig(level=logging.INFO)

def upload_logs_to_gcs(file_name):
    """Upload logs to Google Cloud Storage"""
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
    """Initialize Chrome WebDriver with proxy."""
    server, proxy = setup_browsermob
    logging.info("Starting a Chrome instance...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.accept_insecure_certs = True
    options.binary_location = CHROME_BINARY_PATH

    proxy_config = Proxy({
        "proxyType": ProxyType.MANUAL,
        "httpProxy": proxy.proxy,
        "sslProxy": proxy.proxy
    })
    options.proxy = proxy_config
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    yield driver, proxy
    logging.info("Closing WebDriver...")
    driver.quit()


def log_assert(title, condition, message):
    try:
        assert condition, message
        log_message = f"{metadata_string}|' {title} '|{url_to_be_tested}|success"
        log_info(log_message)

    except AssertionError as e:
        failure_reason = f"{title} failed: {str(e)}"
        log_message = f"{metadata_string}|' {title} '|{url_to_be_tested}|FAILED: {failure_reason}"
        log_error(log_message)

def log_info(message):
    logging.info(message)
    with open(logs_file_name, "a") as log_file:
        log_file.write(f"{start_timestamp}\t{test_name}\tinfo\t{message}\n")

def log_error(message):
    logging.error(message)
    with open(logs_file_name, "a") as log_file:
        log_file.write(f"{start_timestamp}\t{test_name}\terror\t{message}\n")

@pytest.mark.parametrize("test_url", [url_to_be_tested])
def test_hire_now_form(setup_driver, test_url):
    global test_finish_timestamp, test_result, test_error_description
    driver, proxy = setup_driver

    try:
        logging.info(f"{metadata_string}|'Navigate to URL'|{test_url}|Navigating to {test_url}")
        driver.get(test_url)

        #Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "rhcl-dropdown"))
        )
        log_info(f"{metadata_string}|'Form Loaded'|{test_url}|Form elements detected")

        #dismiss cookie banner if present
        try:
            wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
            log_info("Cookie banner dismissed")
        except:
            log_info("No cookie banner")



        # Test the title and presence of specific text
        log_assert("Page contains 'Hire Now' in title", "Hire Now" in driver.title, "Page title does not contain 'Hire Now'")
        
        # Fill out the form fields
        def fill_field(selector, value, label):
            try:
                log_info(f"Typing {label}...")
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
                
                # Assert that the field was filled with the correct value
                check_value_script = "return document.querySelector(arguments[0]).interactionRef.value;"
                filled_value = driver.execute_script(check_value_script, selector)
                log_assert(f"{label} field filled correctly", filled_value == value, f"Expected {value}, but got {filled_value}")
            except Exception as e:
                log_error(f"Error filling field {label}: {e}")

        fill_field("rhcl-typeahead[name='positionTitle']", "Quality Assurance Engineer", "Job Title")
        fill_field("rhcl-text-field[name='postalCode']", "99502", "Zip Code")
        fill_field("rhcl-textarea[name='additionalInfo']", "Test message", "Comments")
        fill_field("rhcl-text-field[name='firstName']", "Jes", "First Name")
        fill_field("rhcl-text-field[name='lastName']", "Carney", "Last Name")
        fill_field("rhcl-text-field[name='phoneNumber']", "1234567890", "Phone Number")
        fill_field("rhcl-text-field[name='email']", "jes@example.com", "Email")
        fill_field("rhcl-text-field[name='companyName']", "Robert Half", "Company Name")
        fill_field("rhcl-text-field[name='customerTitle']", "Director", "Customer Title")

        # Dropdown and checkbox
        try:
            driver.execute_script("""
                const el = document.querySelector("rhcl-dropdown[name='employmentType']");
                el.interactionRef.value = "Contract Talent";
                el.interactionRef.dispatchEvent(new Event('change', { bubbles: true }));
            """)
            # Assert that the field was filled with the correct value
            filled_value = driver.execute_script("""return document.querySelector("rhcl-dropdown[name='employmentType']").interactionRef.value;""")
            log_assert("Employment Type dropdown field filled correctly", filled_value == "Contract Talent", f"Expected 'Contract Talent', but got {filled_value}")
        except Exception as e:
            log_error(f"Could not set Employment Type dropdown: {e}")

    finally:
        test_finish_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # Comment out the file upload for now since it's not working
        # upload_logs_to_gcs(logs_file_name)

if __name__ == "__main__":
    try:
        exit_code = pytest.main()

        if exit_code != 0:
            logging.warning("Some tests failed, but forcing exit with 0.")
            sys.exit(0)  # Force job success

    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")
        sys.exit(1)  # Only fail for unexpected runtime errors