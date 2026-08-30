test_that("semantic job helpers validate export and reproducibility formats before network", {
  expect_error(
    hdp_semantic_job_export("job", format = "xlsx"),
    "json, csv or geojson"
  )
  expect_error(
    hdp_semantic_reproducibility("bash", sources = "world-bank-health"),
    "r or python"
  )
})

test_that("semantic job payload preserves project context", {
  payload <- .hdp_semantic_payload(
    c("world-bank-health", "world-bank-health"),
    "malaria", "RWA", "2020-01-01", "2025-12-31", 25L,
    "00000000-0000-4000-8000-000000000001"
  )
  expect_equal(payload$sources, "world-bank-health")
  expect_equal(payload$location, "RWA")
  expect_match(payload$project_id, "0001$")
})
