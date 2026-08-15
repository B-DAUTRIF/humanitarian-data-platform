FROM gcc:14-bookworm AS build
WORKDIR /src
COPY runner.c .
RUN gcc -std=c17 -O2 -Wall -Wextra -Werror runner.c -o hdp-runner

FROM rocker/r-ver:4.4.3
COPY --from=build /src/hdp-runner /usr/local/bin/hdp-runner
RUN mkdir -p /spool /tmp && chmod 1777 /spool /tmp
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/hdp-runner"]
