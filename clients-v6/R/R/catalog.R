hdp_catalog <- local({
  cache <- NULL
  function() {
    if (!is.null(cache)) return(cache)
    plain <- system.file("extdata", "operations.json", package="HDPClientsR")
    if (nzchar(plain)) {
      cache <<- jsonlite::fromJSON(plain, simplifyVector=FALSE)
      return(cache)
    }
    legacy <- system.file("extdata", "operations.json.gz", package="HDPClientsR")
    if (!nzchar(legacy)) stop("Catalogue operations.json introuvable")
    con <- gzfile(legacy, "rt", encoding="UTF-8"); on.exit(close(con), add=TRUE)
    txt <- paste(readLines(con, warn=FALSE), collapse="\n")
    cache <<- jsonlite::fromJSON(txt, simplifyVector=FALSE)
    cache
  }
})

hdp_sources <- function() {
  cat <- hdp_catalog(); names(cat$sources)
}

hdp_operations <- function(source=NULL, safe_only=FALSE) {
  ops <- hdp_catalog()$operations
  if (!is.null(source)) ops <- Filter(function(x) identical(x$source, source) || identical(x$source_slug, source), ops)
  if (isTRUE(safe_only)) ops <- Filter(function(x) isTRUE(x$safe_read), ops)
  ops
}

.hdp_operation <- function(operation_id) {
  ops <- hdp_catalog()$operations
  hit <- Filter(function(x) identical(x$id, operation_id), ops)
  if (!length(hit)) stop("Unknown operation_id: ", operation_id)
  hit[[1]]
}
