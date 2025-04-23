PYTHON_VERSION = python3
PIP = pip
TESTS_DIR = tests
RESULTS_DIR = results
DOCKER_IMAGE = selenium-test-env
CONTAINER_NAME = selenium-test-runner
LOGS_DIR = logs

all: build test

build:
	@echo "Building Test Container..."
	@docker stop selenium-container || true
	@docker rm selenium-container || true
	@docker build -t $(DOCKER_IMAGE) -f docker_local_tests/Dockerfile .
	@docker run -d --name selenium-container -p 4444:4444 \
	    -v $(shell pwd):/qa-automation \
	    -v $(shell pwd)/logs:/qa-automation/logs \
	    $(DOCKER_IMAGE)
	@echo "Docker image built."


# test:
# 	@echo "Running all tests inside Docker container..."
# 	@docker exec -it selenium-container bash -c "pytest -s -vv /qa-automation/tests | tee /qa-automation/logs/test_results.log"
# 	@echo "Tests completed. See logs/test_results.log for details."
test:
	@echo "Running all tests inside Docker container..."
	@docker exec -it selenium-container bash -c "pytest -o log_cli=true -o log_cli_level=DEBUG -s -vv /qa-automation/tests | tee -a /qa-automation/logs/test_results.log"
	@echo "Tests completed. See logs/test_results.log for details."

test-specific:
	@echo "Running specific test: $(TEST)"
	@docker exec -it selenium-container bash -c "pytest /qa-automation/$(TEST) | tee /qa-automation/logs/test_results.log"
	@echo "Test completed. See logs/test_results.log for details."

clean:
	@echo "Cleaning up logs..."
	@docker exec -it selenium-container bash -c "rm -rf /qa-automation/logs/*.log"
	@echo "Logs cleaned."

log:
	@echo "Showing Flask, BrowserMob, Selenium, and Test Results logs..."
	@docker exec -it selenium-container tail -f /qa-automation/logs/selenium.log /qa-automation/logs/test_results.log /qa-automation/server.log 2>/dev/null || docker logs -f selenium-container

help:
	@echo "Available commands:"
	@echo "  make build           - Build the Docker image and install dependencies"
	@echo "  make test            - Run all tests in a Docker container"
	@echo "  make test-specific TEST=<test_path> - Run a specific test"
	@echo "  make clean           - Clean up all test logs"
	@echo "  make log             - Show logs for Flask, BrowserMob, Selenium, and test results"
	@echo "  make help            - Show this help message"
