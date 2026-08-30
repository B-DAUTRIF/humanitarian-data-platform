\name{hdp_semantic_job_create}
\alias{hdp_semantic_job_create}
\alias{hdp_semantic_job}
\alias{hdp_semantic_job_cancel}
\alias{hdp_semantic_job_export}
\alias{hdp_semantic_reproducibility}
\title{Persistent HDP V7 semantic jobs and reproducibility}
\description{Queue, inspect, cancel and export long-running project-aware semantic searches through the local HDP V7 server. Generate secret-free R or Python reproduction scripts.}
\usage{
hdp_semantic_job_create(sources, query = "", location = "", date_from = "",
  date_to = "", result_limit = 25L,
  project_id = "00000000-0000-4000-8000-000000000001",
  base_url = "http://localhost:8080", token = NULL)
hdp_semantic_job(job_id, base_url = "http://localhost:8080", token = NULL)
hdp_semantic_job_cancel(job_id, base_url = "http://localhost:8080", token = NULL)
hdp_semantic_job_export(job_id, format = "json",
  base_url = "http://localhost:8080", token = NULL)
hdp_semantic_reproducibility(language, sources, query = "", location = "",
  date_from = "", date_to = "", result_limit = 25L,
  project_id = "00000000-0000-4000-8000-000000000001",
  base_url = "http://localhost:8080", token = NULL)
}
\arguments{
  \item{sources}{Character vector of HDP source identifiers.}
  \item{query}{Free-text thematic query.}
  \item{location}{Country/area name, ISO3 or M49 value.}
  \item{date_from,date_to}{Optional ISO dates in YYYY-MM-DD format.}
  \item{result_limit}{Maximum results per source, from 1 to 100.}
  \item{project_id}{HDP project UUID.}
  \item{base_url}{Local HDP server URL.}
  \item{token}{Optional local HDP authentication token.}
  \item{job_id}{Semantic job UUID.}
  \item{format}{Export format: json, csv or geojson. GeoJSON is produced only when native geometries exist.}
  \item{language}{Reproducibility language: r or python.}
}
\value{Job functions return parsed HDP job metadata. Export and reproducibility functions return parsed JSON or text depending on the requested representation.}
\details{The functions never query providers directly. HDP remains authoritative for project settings, verified semantic mappings, source status, provenance and safety. Generated scripts obtain credentials from environment variables instead of embedding secrets.}
