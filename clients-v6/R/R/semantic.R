#' Build or execute an HDP V7 semantic query
#'
#' These helpers call the local HDP server so project configuration, semantic
#' mappings, provenance, source status and safety controls remain authoritative.
#'
#' @param sources Character vector of HDP source identifiers.
#' @param query Free-text thematic query.
#' @param location Country/area name, ISO3 or M49 value understood by HDP.
#' @param date_from,date_to ISO dates (YYYY-MM-DD) or empty strings.
#' @param result_limit Maximum number of returned items per source (1..100).
#' @param project_id HDP project UUID. Defaults to the historical default project.
#' @param base_url Local HDP HTTP endpoint.
#' @param token Optional HDP local token for local-token authentication mode.
#' @return Parsed JSON response as an R list.
#' @export
hdp_semantic_plan <- function(
  sources,
  query = "",
  location = "",
  date_from = "",
  date_to = "",
  result_limit = 25L,
  project_id = "00000000-0000-4000-8000-000000000001",
  base_url = "http://localhost:8080",
  token = NULL
) {
  .hdp_semantic_call(
    "plan", sources, query, location, date_from, date_to,
    result_limit, project_id, base_url, token
  )
}

#' @rdname hdp_semantic_plan
#' @export
hdp_semantic_search <- function(
  sources,
  query = "",
  location = "",
  date_from = "",
  date_to = "",
  result_limit = 25L,
  project_id = "00000000-0000-4000-8000-000000000001",
  base_url = "http://localhost:8080",
  token = NULL
) {
  .hdp_semantic_call(
    "search", sources, query, location, date_from, date_to,
    result_limit, project_id, base_url, token
  )
}

.hdp_semantic_payload <- function(
  sources, query, location, date_from, date_to, result_limit, project_id
) {
  sources <- unique(trimws(as.character(sources)))
  sources <- sources[nzchar(sources)]
  if (!length(sources)) stop("sources must contain at least one source", call. = FALSE)
  result_limit <- as.integer(result_limit)
  if (is.na(result_limit) || result_limit < 1L || result_limit > 100L) {
    stop("result_limit must be between 1 and 100", call. = FALSE)
  }
  list(
    project_id = as.character(project_id),
    sources = sources,
    query = as.character(query),
    location = as.character(location),
    date_from = as.character(date_from),
    date_to = as.character(date_to),
    result_limit = result_limit
  )
}

.hdp_semantic_call <- function(
  operation, sources, query, location, date_from, date_to,
  result_limit, project_id, base_url, token
) {
  payload <- .hdp_semantic_payload(
    sources, query, location, date_from, date_to, result_limit, project_id
  )
  request <- httr2::request(paste0(sub("/$", "", base_url), "/api/semantic/", operation))
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
  request <- httr2::req_body_json(request, payload, auto_unbox = TRUE)
  response <- httr2::req_perform(request)
  httr2::resp_body_json(response, simplifyVector = FALSE)
}
