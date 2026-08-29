.hdp_records <- function(response) {
  d <- response$data
  if (is.data.frame(d)) return(d)
  if (is.list(d) && !is.null(names(d))) {
    for (nm in c("data","results","result","value","features")) {
      v <- d[[nm]]
      if (is.data.frame(v)) return(v)
      if (is.list(v) && length(v)) {
        tab <- tryCatch(jsonlite::rbind_pages(v), error=function(e) NULL)
        if (!is.null(tab)) return(tab)
        return(data.frame(json=vapply(v,jsonlite::toJSON,"",auto_unbox=TRUE,null="null"),stringsAsFactors=FALSE))
      }
    }
    return(data.frame(json=jsonlite::toJSON(d,auto_unbox=TRUE,null="null"),stringsAsFactors=FALSE))
  }
  if (is.list(d) && length(d)) {
    tab <- tryCatch(jsonlite::rbind_pages(d), error=function(e) NULL)
    if (!is.null(tab)) return(tab)
  }
  data.frame(value=as.character(d),stringsAsFactors=FALSE)
}
hdp_export_json <- function(response,path) { jsonlite::write_json(response$data,path,pretty=TRUE,auto_unbox=TRUE,null="null"); invisible(path) }
hdp_export_csv <- function(response,path) { utils::write.csv(.hdp_records(response),path,row.names=FALSE,fileEncoding="UTF-8"); invisible(path) }
hdp_export_xlsx <- function(response,path) { writexl::write_xlsx(list(data=.hdp_records(response),provenance=data.frame(field=c("source","operation_id","method","url","status_code","elapsed_seconds"),value=c(response$source,response$operation_id,response$method,response$url,response$status_code,response$elapsed_seconds))),path); invisible(path) }
