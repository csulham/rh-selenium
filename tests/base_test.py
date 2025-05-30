import pytest
import psutil
import datetime
import uuid
import logging
import urllib.parse
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from google.cloud import storage
import time

# Common constants
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver-linux64/chromedriver"
CHROME_BINARY_PATH = "/opt/google/chrome/chrome-linux64/chrome"

@pytest.fixture(scope="module", autouse=True)
def setup_browsermob():
    """Start BrowserMob Proxy before tests and stop after."""
    logging.info("Killing all browsermob-proxy processes...")
    for proc in psutil.process_iter():
        if 'proxy' in proc.name() or 'browser' in proc.name():
            proc.kill()

    logging.info("Starting BrowserMob Proxy...")
    server = Server(path="/drivers/browsermob-proxy-2.1.4/bin/browsermob-proxy")
    try:
        server.start()
        time.sleep(5)
    except Exception as e:
        logging.error(f"Failed to start BrowserMob Proxy: {e}")
        pytest.fail("BrowserMob Proxy failed to start.")

    proxy = server.create_proxy()
    # Configure proxy to capture all content types
    proxy.new_har(options={
        'captureHeaders': True,
        'captureContent': True,
        'captureBinaryContent': True
    })
    
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
    options.add_argument("--enable-javascript")
    options.add_argument("--enable-cookies")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1980,1024")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    
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

class BaseTest:    
    def setup_method(self, method):
        """Initialize test instance attributes"""
        self.start_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.test_finish_timestamp = ""
        self.test_result = "success"
        self.test_error_description = ""
        self.run_id = uuid.uuid4()
        self.logs_file_name = f"{self.start_timestamp}_logs_automationqa.txt"

    def get_metadata_string(self, test_suite, test_suite_version, test_case_name, test_case_version):
        return f'{test_suite}|{test_suite_version}|{test_case_name}|{test_case_version}'

    def log_info(self, message):
        logging.info(message)
        with open(self.logs_file_name, "a") as log_file:
            log_file.write(f"{self.start_timestamp}\t{self.test_name}\tinfo\t{message}\n")

    def log_error(self, message):
        logging.error(message)
        with open(self.logs_file_name, "a") as log_file:
            log_file.write(f"{self.start_timestamp}\t{self.test_name}\terror\t{message}\n")

    def log_assert(self, title, condition, message):
        try:
            assert condition, message
            log_message = f"{self.metadata_string}|'{title}'|success"
            self.log_info(log_message)
        except AssertionError as e:
            failure_reason = f"{title} failed: {str(e)}"
            log_message = f"{self.metadata_string}|'{title}'|FAILED: {failure_reason}"
            self.log_error(log_message)
            raise

    def upload_logs_to_gcs(self, file_name):
        """Upload logs to Google Cloud Storage"""
        bucket_name = 'automation-qa-logs'
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_name)
        self.log_info(f"File {file_name} uploaded to {bucket_name}.")

    def wait_for_data_layer(self, driver, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            data_layer = driver.execute_script("return window.dataLayer || []")
            if data_layer and len(data_layer) > 0:
                return data_layer
            time.sleep(0.5)
        raise TimeoutError("Timed out waiting for dataLayer to be populated")

    def get_data_layer(self, driver):
        try:
            return self.wait_for_data_layer(driver)
        except TimeoutError as e:
            self.log_error(f"DataLayer not available: {str(e)}")
            return []

    def load_dataLayer_and_dismiss_cookie(self, driver):
        """Wait for page load, refresh for dataLayer, and dismiss cookie banner if present."""
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "rhcl-dropdown"))
        )
  
        #refresh the page to ensure all dataLayer events are loaded. user_id_ga is set on second visit.
        driver.refresh()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "rhcl-dropdown"))
        )
        self.log_info(f"{self.metadata_string}|Form Loaded, form elements detected")

        # Handle OneTrust cookie consent if present
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-close-btn-container"))
            ).click()
            self.log_info(f"{self.metadata_string}|Cookie banner dismissed")
        except:
            self.log_info(f"{self.metadata_string}|No cookie banner detected")

    def validate_datalayer_event(self, data_layer, event_name, expected_properties, check_user_ids=True, max_retries=3):
        """Generic method to validate datalayer events
        Args:
            data_layer: The dataLayer from the page
            event_name: Name of the GA4 event to validate (e.g. 'page_view', 'phone_click')
            expected_properties: Dictionary of expected key-value pairs in the event
            check_user_ids: Boolean indicating whether to check for user_id_ga and user_id_tealium
            max_retries: Number of retries for checking dataLayer
        """
        for attempt in range(max_retries):
            self.log_info(f"Validating datalayer {event_name} event (Attempt {attempt+1}/{max_retries})...")
            if not data_layer:
                assert False, "DataLayer is empty"
                
            for entry in data_layer:
                if isinstance(entry, list) and entry[0] == "event" and entry[1] == event_name:
                    data = entry[2]
                    passed = True
                    for k, v in expected_properties.items():
                        self.log_assert(f"Checking dataLayer for {k}", k in data, f"Key '{k}' not found in dataLayer")
                        self.log_assert(f"Checking dataLayer for {k}=={v}", data[k] == v, f"Value for '{k}' does not match expected value. Expected: {v}, Found: {data[k]}")

                    # Check user IDs if required
                    if check_user_ids:
                        self.log_assert("Checking user_id_ga", data.get('user_id_ga') is not None, "user_id_ga not found in dataLayer.")
                        self.log_assert("Checking user_id_tealium", data.get('user_id_tealium') is not None, "user_id_tealium not found in dataLayer.")
                    
                    return passed

            if attempt < max_retries - 1:
                self.log_info(f"GA4 {event_name} event not found, retrying...")
                time.sleep(5)
            
        assert False, f"GA4 {event_name} event not found in dataLayer after {max_retries} attempts"

    def validate_ga4_collect_event(self, proxy, event_name, expected_properties, max_retries=3):
        """Generic method to validate GA4 collect network requests in HAR logs
        Args:
            proxy: The proxy instance from setup_driver
            event_name: Name of the GA4 event to validate (e.g. 'page_view', 'phone_click')            
            expected_properties: Dictionary of expected key-value pairs in the request URL
            max_retries: Number of retries for checking HAR logs
        """
        target_url = "https://www.google-analytics.com/g/collect"
        request_found = False
        actual_request_url = None
        all_requests = []

        for attempt in range(max_retries):
            self.log_info(f"Checking HAR logs (Attempt {attempt+1}/{max_retries})...")
            har_dict = proxy.har  # Get the latest network logs
            all_requests = []  # Reset all_requests for each attempt

            for entry in har_dict['log']['entries']:
                request = entry['request']
                all_requests.append(request['url'])

                if target_url in request['url'] and f"en={event_name}" in request['url']:
                    actual_request_url = request['url']
                    self.log_info(f"Request sent to: {actual_request_url}")
                    request_found = True
                    break

            if request_found:
                break  # Exit loop if request is found
            self.log_info("GA4 collect request not found, retrying...")
            time.sleep(5)  # Wait before retrying

        # If no match found, show the requests we were searching through
        if not request_found:
            self.log_info("=== No matching GA4 request found. All captured requests: ===")
            for url in all_requests:
                self.log_info(f"URL: {url}")

        self.log_assert(f"GA4 request found in HAR logs: {actual_request_url}", request_found, f"GA4 collect confirmation: no request found to {target_url}")
        
        # Validate expected parameters in the request URL
        for param, expected_value in expected_properties.items():
            param_exists = f"{param}=" in actual_request_url
            self.log_assert(
                f"Checking GA4 request for {param}",
                param_exists,
                f"Parameter '{param}' not found in GA4 request URL"
            )
            # Extract the actual value from the URL
            actual_value = urllib.parse.parse_qs(urllib.parse.urlparse(actual_request_url).query).get(param, [None])[0]
            self.log_assert(
                f"Checking GA4 request for {param}=={expected_value}",
                actual_value == expected_value,
                f"Value for '{param}' does not match expected value. Expected: {expected_value}, Found: {actual_value}"
            )

    def get_request_response_payload(self, proxy, url_path, max_retries=3):
        """
        Collect request and response payloads from HAR logs for a specific URL path.
        
        Args:
            proxy: The BrowserMob proxy instance
            url_path: The URL path to search for in the HAR logs
            max_retries: Number of times to retry checking the HAR logs
            
        Returns:
            tuple: (request_payload, response_payload) if found, (None, None) if not found
        """
        for attempt in range(max_retries):
            har = proxy.har
            
            if not har or 'log' not in har or 'entries' not in har['log']:
                self.log_info(f"No HAR entries found, attempt {attempt + 1}/{max_retries}")
                time.sleep(5)
                continue
                
            for entry in har['log']['entries']:
                request = entry.get('request', {})
                response = entry.get('response', {})
                
                # Check if this is the request we're looking for
                if url_path in request.get('url', ''):
                    self.log_info(f"Found matching request to {url_path}")
                    
                    # Get request payload
                    request_payload = None
                    if 'postData' in request:
                        request_payload = request['postData'].get('text') or request['postData'].get('params')
                        self.log_info(f"Request payload for {url_path}: {request_payload}")
                    
                    # Get response payload
                    response_payload = None
                    if 'content' in response:
                        response_payload = response['content'].get('text')
                        if response_payload:
                            import base64
                            try:
                                decoded = base64.b64decode(response_payload).decode('utf-8')
                                self.log_info(f"Response payload for {url_path}: {decoded}")
                            except Exception as e:
                                self.log_info(f"Could not decode response payload: {e}")
                                decoded = response_payload
                        else:
                            decoded = None
                            self.log_info(f"No response payload content for {url_path}")
                    
                    return request_payload, decoded
            
            if attempt < max_retries - 1:
                self.log_info(f"Request to {url_path} not found in HAR logs, retrying...")
                time.sleep(5)
        
        self.log_info(f"No matching request found for {url_path} after {max_retries} attempts")
        return None, None
