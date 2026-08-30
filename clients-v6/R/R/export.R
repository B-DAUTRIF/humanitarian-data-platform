.hdp_record_frame <- function(values) {
  if (!is.list(values) || !length(values)) return(NULL)
  if (!all(vapply(values, is.list, logical(1)))) return(NULL)
  scalar_rows <- all(vapply(values, function(row) {
    length(row) > 0 && all(vapply(row, function(value) is.null(value) || (is.atomic(value) && length(value) <= 1), logical(1)))
  }, logical(1)))
  if (!scalar_rows) return(NULL)
  columns <- unique(unlist(lapply(values, names), use.names=FALSE))
  rows <- lapply(values, function(row) {
    out <- setNames(vector("list", length(columns)), columns)
    for (name in columns) out[[name]] <- if (is.null(row[[name]])) NA else row[[name]]
    as.data.frame(out, stringsAsFactors=FALSE, check.names=FALSE)
  })
  do.call(rbind, rows)
}

.hdp_records <- function(response) {
  d <- response$data
  if (is.data.frame(d)) return(d)
  if (is.list(d) && !is.null(names(d))) {
    for (nm in c("data","results","result","value","features")) {
      v <- d[[nm]]
      if (is.data.frame(v)) return(v)
      if (is.list(v) && length(v)) {
        simple <- .hdp_record_frame(v)
        if (!is.null(simple)) return(simple)
        tab <- tryCatch(jsonlite::rbind_pages(v), error=function(e) NULL)
        if (!is.null(tab)) return(tab)
        return(data.frame(json=vapply(v,jsonlite::toJSON,"",auto_unbox=TRUE,null="null"),stringsAsFactors=FALSE))
      }
    }
    return(data.frame(json=jsonlite::toJSON(d,auto_unbox=TRUE,null="null"),stringsAsFactors=FALSE))
  }
  if (is.list(d) && length(d)) {
    simple <- .hdp_record_frame(d)
    if (!is.null(simple)) return(simple)
    tab <- tryCatch(jsonlite::rbind_pages(d), error=function(e) NULL)
    if (!is.null(tab)) return(tab)
  }
  data.frame(value=as.character(d),stringsAsFactors=FALSE)
}
hdp_export_json <- function(response,path) { jsonlite::write_json(response$data,path,pretty=TRUE,auto_unbox=TRUE,null="null"); invisible(path) }
hdp_export_csv <- function(response,path) { utils::write.csv(.hdp_records(response),path,row.names=FALSE,fileEncoding="UTF-8"); invisible(path) }
hdp_export_xlsx <- function(response,path) { writexl::write_xlsx(list(data=.hdp_records(response),provenance=data.frame(field=c("source","operation_id","method","url","status_code","elapsed_seconds"),value=c(response$source,response$operation_id,response$method,response$url,response$status_code,response$elapsed_seconds))),path); invisible(path) }
