FROM python:3.12-slim

ENV LANG C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# Force playwright version compatible with python 3.12
RUN pip install --no-cache-dir playwright==1.40.0 requests && \
    playwright install --with-deps chromium

WORKDIR /app

# Create package structure
RUN mkdir -p /app/antel_pkg
RUN touch /app/antel_pkg/__init__.py

# Copy scraper code into package
COPY custom_components/antel_consumo/antel_scraper.py /app/antel_pkg/antel_scraper.py
COPY custom_components/antel_consumo/const.py /app/antel_pkg/const.py

# Copy add-on main script and runner
COPY antel_addon/main.py /app/main.py
COPY antel_addon/run.sh /app/run.sh

RUN chmod a+x /app/run.sh

CMD [ "/app/run.sh" ]
