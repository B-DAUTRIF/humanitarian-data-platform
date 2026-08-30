.hdp_loc <- function(raw, method) {
  s <- tolower(raw %||% "")
  if (grepl("path",s) && !grepl("query",s)) return("path")
  if (grepl("header",s) && !grepl("query",s)) return("header")
  if (grepl("formdata|formulaire",s)) return("form")
  if (grepl("body|json|data_dict",s)) {
    if (grepl("query",s) && identical(method,"GET")) return("query")
    return("body")
  }
  "query"
}
`%||%` <- function(x,y) if (is.null(x) || !length(x)) y else x
.hdp_required <- function(x) tolower(trimws(as.character(x %||% ""))) %in% c("oui","yes","true","1","required","obligatoire")
.hdp_scalar <- function(x) if (is.list(x)) jsonlite::toJSON(x,auto_unbox=TRUE,null="null") else x
.hdp_has_default <- function(x) {
  if (is.null(x) || !length(x)) return(FALSE)
  any(nzchar(trimws(as.character(unlist(x, recursive=TRUE, use.names=FALSE)))))
}

.hdp_auth <- function(source, values) {
  if (identical(source,"ReliefWeb") && is.null(values$appname) && nzchar(Sys.getenv("RELIEFWEB_APPNAME"))) values$appname <- Sys.getenv("RELIEFWEB_APPNAME")
  if (identical(source,"HDX HAPI") && is.null(values$app_identifier) && nzchar(Sys.getenv("HDX_HAPI_APP_IDENTIFIER"))) values$app_identifier <- Sys.getenv("HDX_HAPI_APP_IDENTIFIER")
  if (identical(source,"DHS Program") && is.null(values$apiKey) && nzchar(Sys.getenv("DHS_API_KEY"))) values$apiKey <- Sys.getenv("DHS_API_KEY")
  values
}

hdp_preview <- function(operation_id, params=list(), method=NULL, extra_path=list()) {
  op <- .hdp_operation(operation_id); methods <- unlist(op$methods)
  if (is.null(method)) {
    method <- if ("GET" %in% methods) "GET" else methods[[1]]
    body_names <- vapply(Filter(function(p) grepl("body",tolower(p$location %||% "")), op$parameters), `[[`, "", "name")
    if (length(intersect(names(params),body_names)) && "POST" %in% methods) method <- "POST"
  }
  method <- toupper(method); if (!method %in% methods) stop("Method not allowed: ", method)
  values <- .hdp_auth(op$source, params); specs <- setNames(op$parameters, vapply(op$parameters, `[[`, "", "name"))
  for (nm in names(specs)) {
    sp <- specs[[nm]]
    if (is.null(values[[nm]]) && .hdp_has_default(sp$default)) values[[nm]] <- sp$default
    if (.hdp_required(sp$required) && is.null(values[[nm]])) stop("Missing required parameter: ",nm)
  }
  path_values <- extra_path; query <- list(); body <- list(); headers <- list(Accept="application/json, text/csv;q=0.9, */*;q=0.5", `User-Agent`="HDP-Clients-R/6.0.0"); form <- list()
  for (nm in names(values)) {
    val <- values[[nm]]; if (is.null(val) || identical(val,"")) next
    loc <- .hdp_loc((specs[[nm]] %||% list(location="query"))$location, method)
    if (loc=="path") path_values[[nm]] <- val else if (loc=="body") body[[nm]] <- val else if (loc=="header") headers[[nm]] <- as.character(val) else if (loc=="form") form[[nm]] <- val else query[[nm]] <- val
  }
  endpoint <- op$endpoint; ph <- regmatches(endpoint, gregexpr("\\{[^{}]+\\}", endpoint))[[1]]
  if (length(ph) && ph[[1]] != "") for (token in ph) {
    nm <- substring(token,2,nchar(token)-1); val <- path_values[[nm]] %||% values[[nm]]
    if (is.null(val)) stop("Missing path placeholder ", token, "; supply params or extra_path")
    endpoint <- sub(token, utils::URLencode(as.character(val), reserved=TRUE), endpoint, fixed=TRUE)
  }
  if (identical(op$source,"HDX / CKAN")) { tok <- Sys.getenv("HDX_API_TOKEN"); if (!nzchar(tok)) tok <- Sys.getenv("CKAN_API_TOKEN"); if (nzchar(tok)) headers$Authorization <- tok }
  list(operation=op,method=method,url=paste0(sub("/$","",op$base_url),"/",sub("^/","",endpoint)),query=query,body=body,form=form,headers=headers)
}

hdp_request <- function(operation_id, params=list(), method=NULL, extra_path=list(), allow_unsafe=FALSE) {
  op <- .hdp_operation(operation_id)
  if (!isTRUE(op$safe_read) && !isTRUE(allow_unsafe)) stop("Operation write/administration blocked. Set allow_unsafe=TRUE explicitly.")
  p <- hdp_preview(operation_id,params,method,extra_path)
  req <- httr2::request(p$url)
  req <- httr2::req_method(req,p$method)
  req <- do.call(httr2::req_headers, c(list(req), p$headers))
  req <- httr2::req_timeout(req,45)
  if (length(p$query)) req <- do.call(httr2::req_url_query, c(list(req), p$query))
  if (length(p$body)) req <- httr2::req_body_json(req,p$body,auto_unbox=TRUE)
  if (length(p$form)) req <- do.call(httr2::req_body_form, c(list(req), p$form))
  started <- proc.time()[[3]]; resp <- httr2::req_perform(req); elapsed <- proc.time()[[3]]-started
  raw <- httr2::resp_body_string(resp); ct <- tolower(httr2::resp_header(resp,"content-type") %||% "")
  data <- raw
  if (grepl("json",ct)) data <- tryCatch(jsonlite::fromJSON(raw,simplifyVector=FALSE),error=function(e) raw)
  structure(list(source=op$source,operation_id=operation_id,method=p$method,url=httr2::resp_url(resp),status_code=httr2::resp_status(resp),headers=httr2::resp_headers(resp),data=data,raw_text=raw,elapsed_seconds=elapsed),class="hdp_response")
}
