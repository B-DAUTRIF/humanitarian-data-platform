\name{HDPClientsR}
\alias{HDPClientsR}
\alias{hdp_catalog}
\alias{hdp_sources}
\alias{hdp_operations}
\alias{hdp_preview}
\alias{hdp_request}
\alias{hdp_export_json}
\alias{hdp_export_csv}
\alias{hdp_export_xlsx}
\alias{hdp_hdx}
\alias{hdp_reliefweb}
\alias{hdp_who_gho}
\alias{hdp_world_bank_health}
\alias{hdp_unicef_sdmx}
\alias{hdp_un_sdg}
\alias{hdp_dhs}
\alias{hdp_hdx_hapi}
\alias{hdp_unhcr}
\alias{hdp_gdacs}
\title{HDP Clients R}
\description{Inventory-driven R clients for the ten API source families exposed by Humanitarian Data Platform V6.}
\usage{
hdp_catalog()
hdp_sources()
hdp_operations(source = NULL, safe_only = FALSE)
hdp_preview(operation_id, params = list(), method = NULL, extra_path = list())
hdp_request(operation_id, params = list(), method = NULL, extra_path = list(), allow_unsafe = FALSE)
hdp_export_json(response, path)
hdp_export_csv(response, path)
hdp_export_xlsx(response, path)
hdp_hdx()
hdp_reliefweb()
hdp_who_gho()
hdp_world_bank_health()
hdp_unicef_sdmx()
hdp_un_sdg()
hdp_dhs()
hdp_hdx_hapi()
hdp_unhcr()
hdp_gdacs()
}
\arguments{
  \item{source}{Source label or source slug.}
  \item{safe_only}{If true, return only operations classified as read-only.}
  \item{operation_id}{Stable operation identifier from the embedded catalog.}
  \item{params}{Named list of API parameter values.}
  \item{method}{Optional HTTP method when an operation exposes more than one.}
  \item{extra_path}{Named list for endpoint path placeholders not otherwise represented.}
  \item{allow_unsafe}{Explicit opt-in for operations classified as writing or administration.}
  \item{response}{An object returned by \code{hdp_request}.}
  \item{path}{Destination file path.}
}
\value{Catalog and source functions return lists. \code{hdp_preview} returns a serialized request description. \code{hdp_request} returns an object of class \code{hdp_response}. Export functions invisibly return the destination path.}
\details{Credentials are read from environment variables when required. Writing and administrative operations are blocked by default.}
