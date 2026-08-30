#' Persistent HDP V7 semantic jobs
#'
#' Queue, inspect, cancel and export semantic searches through the HDP server.
#' The server remains authoritative for project settings, provenance and provider
#' safety. Credentials are never embedded in generated reproducibility scripts.
#'
#' @inheritParams hdp_semantic_plan
#' @return Parsed job metadata.
#' @export
hdp_semantic_job_create <- function(
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
  payload <- .hdp_semantic_payload(
    sources, query, location, date_from, date_to, result_limit, project_id
  )
  .hdp_local_json("POST", "/api/semantic/jobs", base_url, token, payload)
}

#' @param job_id Semantic job UUID returned by \code{hdp_semantic_job_create}.
#' @param base_url Local HDP server URL.
#' @param token Optional HDP local authentication token.
#' @rdname hdp_semantic_job_create
#' @export
hdp_semantic_job <- function(
  job_id,
  base_url = "http://localhost:8080",
  token = NULL
) {
  .hdp_local_json(
    "GET", paste0("/api/semantic/jobs/", job_id), base_url, token
  )
}

#' @rdname hdp_semantic_job_create
#' @export
hdp_semantic_job_cancel <- function(
  job_id,
  base_url = "http://localhost:8080",
  token = NULL
) {
  .hdp_local_json(
    "POST", paste0("/api/semantic/jobs/", job_id, "/cancel"),
    base_url, token
  )
}

#' @param format One of \code{json}, \code{csv}, or \code{geojson}.
#' @rdname hdp_semantic_job_create
#' @export
hdp_semantic_job_export <- function(
  job_id,
  format = "json",
  base_url = "http://localhost:8080",
  token = NULL
) {
  format <- tolower(format)
  if (!format %in% c("json", "csv", "geojson")) {
    stop("format must be json, csv or geojson", call. = FALSE)
  }
  path <- paste0("/api/semantic/jobs/", job_id, "/export/", format)
  .hdp_local_response("GET", path, base_url, token)
}

#' @param language One of \code{r} or \code{python}.
#' @rdname hdp_semantic_job_create
#' @export
hdp_semantic_reproducibility <- function(
  language,
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
  language <- tolower(language)
  if (!language %in% c("r", "python")) {
    stop("language must be r or python", call. = FALSE)
  }
  payload <- .hdp_semantic_payload(
    sources, query, location, date_from, date_to, result_limit, project_id
  )
  .hdp_local_response(
    "POST", paste0("/api/semantic/jobs/reproducibility/", language),
    base_url, token, payload
  )
}

.hdp_local_request <- function(method, path, base_url, token, payload = NULL) {
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
  if (!is.null(payload)) {
    request <- httr2::req_body_json(request, payload, auto_unbox = TRUE)
  }
  httr2::req_timeout(request, 120)
}

.hdp_local_response <- function(
  method, path, base_url, token, payload = NULL
) {
  request <- .hdp_local_request(method, path, base_url, token, payload)
  response <- httr2::req_perform(request)
  content_type <- tolower(httr2::resp_header(response, "content-type") %||% "")
  if (grepl("json", content_type)) {
    return(httr2::resp_body_json(response, simplifyVector = FALSE))
  }
  httr2::resp_body_string(response)
}

.hdp_local_json <- function(
  method, path, base_url, token, payload = NULL
) {
  result <- .hdp_local_response(method, path, base_url, token, payload)
  if (!is.list(result)) stop("Unexpected non-JSON HDP response", call. = FALSE)
  result
}
