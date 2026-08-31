#' World Bank Health provider descriptor
#' @export
hdp_world_bank_descriptor <- function(base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  hdp_request(base_url, token, "GET", "/api/providers/world-bank-health/descriptor")
}

#' Effective World Bank Health configuration
#' @export
hdp_world_bank_configuration <- function(project_id = NULL, base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  path <- "/api/providers/world-bank-health/configuration/effective"
  if (!is.null(project_id) && nzchar(project_id)) path <- paste0(path, "?project_id=", utils::URLencode(project_id, reserved = TRUE))
  hdp_request(base_url, token, "GET", path)
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
  hdp_request(base_url, token, "POST", "/api/providers/world-bank-health/observations", body)
}

#' Search World Bank metadata through HDP V7
#' @export
hdp_world_bank_metadata <- function(query, source = 2L, page = 1L, per_page = 1000L, language = "en",
                                    base_url = "http://localhost:8080", token = Sys.getenv("HDP_TOKEN", "")) {
  body <- list(query=query, source=source, page=page, per_page=per_page, language=language)
  hdp_request(base_url, token, "POST", "/api/providers/world-bank-health/metadata", body)
}
