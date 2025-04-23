# Use the latest Python base image
FROM --platform=linux/amd64 python:3.10

# Set the working directory inside the container
WORKDIR /qa-automation

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip xvfb \
    ca-certificates gnupg lsb-release \
    firefox-esr && \
    rm -rf /var/lib/apt/lists/*

RUN wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor | tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null
RUN echo "deb https://packages.adoptium.net/artifactory/deb buster main" | tee /etc/apt/sources.list.d/adoptium.list    

RUN apt-get update && \
    apt-get install -y temurin-8-jdk && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/temurin-8-jdk
ENV PATH=$JAVA_HOME/bin:$PATH

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    firefox-esr \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 && \
    rm -rf /var/lib/apt/lists/*

ENV GECKODRIVER_VERSION=v0.35.0
ENV GECKODRIVER_DIR=/usr/local/bin/

# Install GeckoDriver (for Firefox)
RUN wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz && \
    tar -xzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C $GECKODRIVER_DIR && \
    rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz

# Fetch the latest stable Chrome version and install Chrome and ChromeDriver
RUN CHROME_VERSION=$(curl -sSL https://googlechromelabs.github.io/chrome-for-testing/ | awk -F 'Version:' '/Stable/ {print $2}' | awk '{print $1}' | sed 's/<code>//g; s/<\/code>//g') && \
    CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" && \
    echo "Fetching Chrome version: ${CHROME_VERSION}" && \
    curl -sSL ${CHROME_URL} -o /tmp/chrome-linux64.zip && \
    mkdir -p /opt/google/chrome && \
    mkdir -p /usr/local/bin && \
    unzip -q /tmp/chrome-linux64.zip -d /opt/google/chrome && \
    rm /tmp/chrome-linux64.zip

# Install ChromeDriver using the same ${CHROME_VERSION} as Chrome
RUN CHROME_VERSION=$(curl -sSL https://googlechromelabs.github.io/chrome-for-testing/ | awk -F 'Version:' '/Stable/ {print $2}' | awk '{print $1}' | sed 's/<code>//g; s/<\/code>//g') && \
    CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    curl -sSL ${CHROMEDRIVER_URL} -o /tmp/chromedriver-linux64.zip && \
    unzip -q /tmp/chromedriver-linux64.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin && \
    rm /tmp/chromedriver-linux64.zip

ENV BROWSERMOB_PROXY_VERSION=2.1.4

RUN wget https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-${BROWSERMOB_PROXY_VERSION}/browsermob-proxy-${BROWSERMOB_PROXY_VERSION}-bin.zip && \
    unzip browsermob-proxy-${BROWSERMOB_PROXY_VERSION}-bin.zip && \
    mkdir -p /app/drivers && \
    mv browsermob-proxy-${BROWSERMOB_PROXY_VERSION} /app/drivers/ && \
    chmod +x /app/drivers/browsermob-proxy-${BROWSERMOB_PROXY_VERSION}/bin/browsermob-proxy && \
    rm browsermob-proxy-${BROWSERMOB_PROXY_VERSION}-bin.zip && \
    apt-get purge -y --auto-remove wget unzip && \
    rm -rf /var/lib/apt/lists/*

# Set environment variable for PATH
ENV PATH="/qa-automation/drivers/browsermob-proxy-2.1.4/bin:${PATH}"

# Copy all project files
COPY ../ /qa-automation

# Install Python dependencies
RUN pip install --no-cache-dir -r /qa-automation/requirements.txt

# Expose a port for the web server
EXPOSE 5000 8080

# Default command
CMD /qa-automation/drivers/browsermob-proxy-2.1.4/bin/browsermob-proxy --port 8080 & python server.py
