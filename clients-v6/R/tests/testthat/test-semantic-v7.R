test_that("semantic V7 payload is project-aware and deterministic", {
  payload <- HDPClientsR:::.hdp_semantic_payload(
    c("reliefweb", "reliefweb", "world-bank-health"),
    "paludisme", "RWA", "2020-01-01", "2025-12-31", 25L,
    "00000000-0000-4000-8000-000000000001"
  )
  expect_equal(payload$sources, c("reliefweb", "world-bank-health"))
  expect_equal(payload$project_id, "00000000-0000-4000-8000-000000000001")
  expect_equal(payload$location, "RWA")
  expect_equal(payload$result_limit, 25L)
})

test_that("semantic V7 payload rejects unsafe bounds", {
  expect_error(
    HDPClientsR:::.hdp_semantic_payload(character(), "", "", "", "", 25L, "p"),
    "at least one source"
  )
  expect_error(
    HDPClientsR:::.hdp_semantic_payload("reliefweb", "", "", "", "", 101L, "p"),
    "between 1 and 100"
  )
})
