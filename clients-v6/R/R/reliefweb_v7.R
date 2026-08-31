#' ReliefWeb V2 provider helpers through HDP V7
#'
#' These functions call HDP rather than ReliefWeb directly so project settings,
#' provenance, provider error classification and native/normalized representations
#' remain authoritative.
#'
#' @param base_url Local HDP HTTP endpoint.
#' @param token Optional HDP bearer token.
#' @return Parsed JSON as an R list.
#' @export
hdp_reliefweb_descriptor <- function(base_url = "http://localhost:8080", token = NULL) {
  .hdp_reliefweb_api("GET", "/api/providers/reliefweb/descriptor", base_url, token)
}

#' @param project_id Optional HDP project UUID.
#' @rdname hdp_reliefweb_descriptor
#' @export
hdp_reliefweb_configuration <- function(project_id = NULL, base_url = "http://localhost:8080", token = NULL) {
  path <- "/api/providers/reliefweb/configuration/effective"
  if (!is.null(project_id) && nzchar(project_id)) {
    path <- paste0(path, "?project_id=", utils::URLencode(as.character(project_id), reserved = TRUE))
  }
  .hdp_reliefweb_api("GET", path, base_url, token)
}

#' @param content_type ReliefWeb content type.
#' @param parameters Named list of native ReliefWeb parameters represented by HDP.
#' @rdname hdp_reliefweb_descriptor
#' @export
hdp_reliefweb_search_v7 <- function(
  content_type = "reports",
  parameters = list(),
  project_id = NULL,
  base_url = "http://localhost:8080",
  token = NULL
) {
  body <- list(content_type = as.character(content_type), parameters = parameters)
  if (!is.null(project_id) && nzchar(project_id)) body$project_id <- as.character(project_id)
  .hdp_reliefweb_api("POST", "/api/providers/reliefweb/search", base_url, token, body)
}

#' @param item_id ReliefWeb object identifier.
#' @param fields_include,fields_exclude Optional field projection.
#' @param profile Optional ReliefWeb profile.
#' @rdname hdp_reliefweb_descriptor
#' @export
hdp_reliefweb_item <- function(
  content_type,
  item_id,
  fields_include = NULL,
  fields_exclude = NULL,
  profile = NULL,
  project_id = NULL,
  base_url = "http://localhost:8080",
  token = NULL
) {
  parameters <- list()
  if (!is.null(fields_include)) parameters$fields_include <- as.character(fields_include)
  if (!is.null(fields_exclude)) parameters$fields_exclude <- as.character(fields_exclude)
  if (!is.null(profile)) parameters$profile <- as.character(profile)
  body <- list(parameters = parameters)
  if (!is.null(project_id) && nzchar(project_id)) body$project_id <- as.character(project_id)
  path <- paste0(
    "/api/providers/reliefweb/item/",
    utils::URLencode(as.character(content_type), reserved = TRUE), "/",
    utils::URLencode(as.character(item_id), reserved = TRUE)
  )
  .hdp_reliefweb_api("POST", path, base_url, token, body)
}

.hdp_reliefweb_api <- function(method, path, base_url, token, body = NULL) {
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
