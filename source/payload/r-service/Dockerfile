FROM rocker/r-ver:4.4.3

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libcurl4-openssl-dev libssl-dev libsodium-dev \
    && R -q -e "install.packages(c('plumber','jsonlite'), repos='https://cloud.r-project.org')" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY plumber.R .
EXPOSE 8001
CMD ["R", "-q", "-e", "pr <- plumber::plumb('plumber.R'); pr$run(host='0.0.0.0', port=8001)"]
