FROM rocker/r-ver:4.4.3

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libcurl4-openssl-dev libssl-dev libsodium-dev libicu-dev libxml2-dev zlib1g-dev \
    && Rscript -e "install.packages(c('plumber','jsonlite','httr2','writexl','testthat'))" \
    && Rscript -e "stopifnot(requireNamespace('plumber', quietly=TRUE), requireNamespace('jsonlite', quietly=TRUE), requireNamespace('httr2', quietly=TRUE), requireNamespace('writexl', quietly=TRUE), requireNamespace('testthat', quietly=TRUE)); cat(as.character(packageVersion('plumber')), '\n')" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/downloaded_packages

WORKDIR /app
COPY plumber.R .
RUN chown -R 65532:65532 /app
EXPOSE 8001
USER 65532:65532
CMD ["R", "-q", "-e", "pr <- plumber::plumb('plumber.R'); pr$run(host='0.0.0.0', port=8001)"]
