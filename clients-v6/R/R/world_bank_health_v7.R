#' World Bank Health provider descriptor
#' @export
hdp_world_bank_descriptor <- function(base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  .hdp_world_bank_api("GET", "/api/providers/world-bank-health/descriptor", base_url, token)
}

#' Effective World Bank Health configuration
#' @export
hdp_world_bank_configuration <- function(project_id = NULL, base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  path <- "/api/providers/world-bank-health/configuration/effective"
  if (!is.null(project_id) && nzchar(project_id)) path <- paste0(path, "?project_id=", utils::URLencode(project_id, reserved = TRUE))
  .hdp_world_bank_api("GET", path, base_url, token)
}

#' Query World Bank observations through HDP V7
#' @export
hdp_world_bank_observations <- function(country, indicator, date = "", source = 2L, page = 1L, per_page = 50L,
                                        mrv = NULL, mrnev = NULL, gapfill = FALSE, frequency = "",
                                        footnote = FALSE, language = "en", project_id = NULL,
                                        base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  body <- list(country=country, indicator=indicator, date=date, source=source, page=page, per_page=per_page,
               mrv=mrv, mrnev=mrnev, gapfill=gapfill, frequency=frequency, footnote=footnote,
               language=language, project_id=project_id)
  .hdp_world_bank_api("POST", "/api/providers/world-bank-health/observations", base_url, token, body)
}

#' Search World Bank metadata through HDP V7
#' @export
hdp_world_bank_metadata <- function(query, source = 2L, page = 1L, per_page = 1000L, language = "en",
                                    project_id = NULL, base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  body <- list(query=query, source=source, page=page, per_page=per_page, language=language, project_id=project_id)
  .hdp_world_bank_api("POST", "/api/providers/world-bank-health/metadata", base_url, token, body)
}

#' World Bank indicator catalogue through HDP V7
#' @export
hdp_world_bank_indicators <- function(source = 2L, page = 1L, per_page = 1000L, language = "en",
                                      base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  path <- paste0("/api/providers/world-bank-health/indicators?source=", source,
                 "&page=", page, "&per_page=", per_page, "&language=", utils::URLencode(language, reserved = TRUE))
  .hdp_world_bank_api("GET", path, base_url, token)
}

#' World Bank countries and aggregate catalogue through HDP V7
#' @export
hdp_world_bank_countries <- function(identifier = "", page = 1L, per_page = 1000L, language = "en",
                                     base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  path <- paste0("/api/providers/world-bank-health/countries?identifier=", utils::URLencode(identifier, reserved = TRUE),
                 "&page=", page, "&per_page=", per_page, "&language=", utils::URLencode(language, reserved = TRUE))
  .hdp_world_bank_api("GET", path, base_url, token)
}

#' Versioned World Bank geography vocabulary used by HDP
#' @export
hdp_world_bank_geography_vocabulary <- function(language = "en", refresh = FALSE,
                                                base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  path <- paste0("/api/providers/world-bank-health/geography-vocabulary?language=", utils::URLencode(language, reserved = TRUE),
                 "&refresh=", tolower(as.character(isTRUE(refresh))))
  .hdp_world_bank_api("GET", path, base_url, token)
}

#' World Bank indicator metadata through HDP V7
#' @export
hdp_world_bank_indicator_metadata <- function(indicator, source = 2L, language = "en",
                                              base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  path <- paste0("/api/providers/world-bank-health/indicator/", utils::URLencode(indicator, reserved = TRUE),
                 "/metadata?source=", source, "&language=", utils::URLencode(language, reserved = TRUE))
  .hdp_world_bank_api("GET", path, base_url, token)
}

.hdp_world_bank_api <- function(method, path, base_url, token, body = NULL) {
  request <- httr2::request(paste0(sub("/$", "", base_url), path))
  request <- httr2::req_method(request, method)
  request <- httr2::req_headers(
    request,
    Accept = "application/json",
    `User-Agent` = "HDP-Clients-R/7.0.0"
  )
  if (!is.null(token) && nzchar(token)) {
    request <- httr2::req_headers(
      request,
      Authorization = paste("Bearer", token),
      `X-HDP-CSRF` = "1"
    )
  }
  if (!is.null(body)) request <- httr2::req_body_json(request, body, auto_unbox = TRUE)
  response <- httr2::req_perform(request)
  httr2::resp_body_json(response, simplifyVector = FALSE)
}
