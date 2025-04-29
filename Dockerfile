# Use the latest Python base image
FROM debian:buster-slim

# Set the working directory inside the container
WORKDIR /qa-automation

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget tar curl unzip xvfb apt-transport-https software-properties-common \
    ca-certificates gnupg2 lsb-release firefox-esr && \
    rm -rf /var/lib/apt/lists/*

RUN wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor | tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null
RUN echo "deb https://packages.adoptium.net/artifactory/deb buster main" | tee /etc/apt/sources.list.d/adoptium.list

RUN apt-get update && \
    apt-get install -y temurin-8-jdk && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/temurin-8-jdk
ENV PATH=$JAVA_HOME/bin:$PATH

RUN java -version

# Python
# Install required dependencies for building Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    zlib1g-dev \
    liblzma-dev \
    tk-dev \
    libgdbm-dev && \
    rm -rf /var/lib/apt/lists/*

# Download and install Python 3.10.11
RUN wget https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tgz && \
    tar -xzf Python-3.10.11.tgz && \
    cd Python-3.10.11 && \
    ./configure --enable-optimizations && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.10.11 Python-3.10.11.tgz

# Create a symlink for python
RUN ln -s /usr/local/bin/python3.10 /usr/bin/python

# Verify Python installation
RUN python --version

# Set Python 3.10 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1

# Install pip for Python 3.10
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py && \
    rm get-pip.py

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    firefox-esr \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 && \
    rm -rf /var/lib/apt/lists/*

RUN firefox --version

ENV GECKODRIVER_VERSION=v0.35.0
ENV GECKODRIVER_DIR=/usr/local/bin/

# Install GeckoDriver (for Firefox)
RUN wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz && \
    tar -xzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C $GECKODRIVER_DIR && \
    rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz

RUN geckodriver --version

ENV BROWSERMOB_PROXY_VERSION=2.1.4

RUN wget https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-${BROWSERMOB_PROXY_VERSION}/browsermob-proxy-${BROWSERMOB_PROXY_VERSION}-bin.zip && \
    unzip browsermob-proxy-${BROWSERMOB_PROXY_VERSION}-bin.zip && \
    mkdir -p /drivers && \
    mv browsermob-proxy-${BROWSERMOB_PROXY_VERSION} /drivers/ && \
    chmod +x /drivers/browsermob-proxy-${BROWSERMOB_PROXY_VERSION}/bin/browsermob-proxy && \
    rm browsermob-proxy-${BROWSERMOB_PROXY_VERSION}-bin.zip && \
    apt-get purge -y --auto-remove wget unzip && \
    rm -rf /var/lib/apt/lists/*


RUN mkdir -p /qa-automation/logs

# Copy all project files
COPY ../ /qa-automation

# RUN cd /qa-automation/drivers && \
#     chmod +x /qa-automation/drivers/browsermob-proxy-2.1.4/bin/browsermob-proxy && \
#     ls -l /qa-automation/drivers/

# # Set environment variable for PATH
# ENV PATH="/qa-automation/drivers/browsermob-proxy-2.1.4/bin:${PATH}"

# Install Python dependencies
RUN pip install --no-cache-dir -r /qa-automation/requirements.txt

# Default command
CMD ["pytest", "/qa-automation/tests"] 
