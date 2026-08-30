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
\alias{hdp_semantic_plan}
\alias{hdp_semantic_search}
\title{HDP Clients R V7}
\description{Inventory-driven R clients for the API source families exposed by Humanitarian Data Platform, including the project-aware HDP V7 semantic router.}
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
hdp_semantic_plan(
  sources, query = "", location = "", date_from = "", date_to = "",
  result_limit = 25L,
  project_id = "00000000-0000-4000-8000-000000000001",
  base_url = "http://localhost:8080", token = NULL
)
hdp_semantic_search(
  sources, query = "", location = "", date_from = "", date_to = "",
  result_limit = 25L,
  project_id = "00000000-0000-4000-8000-000000000001",
  base_url = "http://localhost:8080", token = NULL
)
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
  \item{sources}{Character vector of HDP source identifiers.}
  \item{query}{Free-text thematic query.}
  \item{location}{Country or area name, ISO3 or M49 value interpreted by HDP.}
  \item{date_from, date_to}{Optional ISO dates in YYYY-MM-DD format.}
  \item{result_limit}{Maximum results per source, from 1 to 100.}
  \item{project_id}{HDP project UUID whose source configuration is authoritative.}
  \item{base_url}{Local HDP server URL.}
  \item{token}{Optional local HDP authentication token.}
}
\value{Catalog and source functions return lists. \code{hdp_preview} returns a serialized request description. \code{hdp_request} returns an object of class \code{hdp_response}. Semantic functions return the parsed HDP V7 JSON plan or result, including per-source status and provenance. Export functions invisibly return the destination path.}
\details{Credentials are read from environment variables when required. Writing and administrative provider operations are blocked by default. Semantic queries go through HDP rather than bypassing it, preserving project configuration, verified mappings, status semantics and provenance.}
