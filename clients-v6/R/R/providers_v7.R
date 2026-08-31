#' Query one of the six specialized HDP V7 provider APIs
#'
#' @param provider One of dhs, gdacs, un-sdg, unhcr, unicef-sdmx, who-gho.
#' @param operation Provider-native operation from the provider descriptor.
#' @param parameters Named list of operation parameters.
#' @param project_id Optional HDP project UUID.
#' @param base_url Local HDP server URL.
#' @param token Optional local-token authentication token.
#' @return Parsed JSON response.
#' @export
hdp_provider_query_v7 <- function(provider, operation, parameters = list(), project_id = NULL,
                                  base_url = "http://localhost:8080", token = NULL) {
  allowed <- c("dhs", "gdacs", "un-sdg", "unhcr", "unicef-sdmx", "who-gho")
  provider <- as.character(provider)[1]
  if (!provider %in% allowed) stop("Unsupported specialized provider", call. = FALSE)
  payload <- list(operation = as.character(operation)[1], parameters = parameters)
  if (!is.null(project_id) && nzchar(as.character(project_id))) payload$project_id <- as.character(project_id)
  request <- httr2::request(paste0(sub("/$", "", base_url), "/api/providers/", provider, "/query"))
  request <- httr2::req_headers(request, Accept = "application/json", `User-Agent` = "HDP-Clients-R/7.0.0")
  if (!is.null(token) && nzchar(token)) {
    request <- httr2::req_headers(request, Authorization = paste("Bearer", token), `X-HDP-CSRF` = "1")
  }
  request <- httr2::req_body_json(request, payload, auto_unbox = TRUE)
  response <- httr2::req_perform(request)
  httr2::resp_body_json(response, simplifyVector = FALSE)
}

#' @rdname hdp_provider_query_v7
#' @export
hdp_dhs_v7 <- function(operation = "list_indicators", parameters = list(), project_id = NULL, base_url = "http://localhost:8080", token = NULL) {
  hdp_provider_query_v7("dhs", operation, parameters, project_id, base_url, token)
}

#' @rdname hdp_provider_query_v7
#' @export
hdp_gdacs_v7 <- function(operation = "search_events", parameters = list(), project_id = NULL, base_url = "http://localhost:8080", token = NULL) {
  hdp_provider_query_v7("gdacs", operation, parameters, project_id, base_url, token)
}

#' @rdname hdp_provider_query_v7
#' @export
hdp_un_sdg_v7 <- function(operation = "list_indicators", parameters = list(), project_id = NULL, base_url = "http://localhost:8080", token = NULL) {
  hdp_provider_query_v7("un-sdg", operation, parameters, project_id, base_url, token)
}

#' @rdname hdp_provider_query_v7
#' @export
hdp_unhcr_v7 <- function(operation = "population", parameters = list(), project_id = NULL, base_url = "http://localhost:8080", token = NULL) {
  hdp_provider_query_v7("unhcr", operation, parameters, project_id, base_url, token)
}

#' @rdname hdp_provider_query_v7
#' @export
hdp_unicef_sdmx_v7 <- function(operation = "list_dataflows", parameters = list(), project_id = NULL, base_url = "http://localhost:8080", token = NULL) {
  hdp_provider_query_v7("unicef-sdmx", operation, parameters, project_id, base_url, token)
}

#' @rdname hdp_provider_query_v7
#' @export
hdp_who_gho_v7 <- function(operation = "list_indicators", parameters = list(), project_id = NULL, base_url = "http://localhost:8080", token = NULL) {
  hdp_provider_query_v7("who-gho", operation, parameters, project_id, base_url, token)
}
