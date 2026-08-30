test_that("every V6 source exposes at least one operation", {
  expect_gt(length(hdp_hdx()), 0)
  expect_gt(length(hdp_reliefweb()), 0)
  expect_gt(length(hdp_who_gho()), 0)
  expect_gt(length(hdp_world_bank_health()), 0)
  expect_gt(length(hdp_unicef_sdmx()), 0)
  expect_gt(length(hdp_un_sdg()), 0)
  expect_gt(length(hdp_dhs()), 0)
  expect_gt(length(hdp_hdx_hapi()), 0)
  expect_gt(length(hdp_unhcr()), 0)
  expect_gt(length(hdp_gdacs()), 0)
})

test_that("operation identifiers are unique and safe filtering is coherent", {
  operations <- hdp_operations()
  ids <- vapply(operations, `[[`, "", "id")
  expect_false(anyDuplicated(ids) > 0)

  safe <- hdp_operations(safe_only = TRUE)
  expect_gt(length(safe), 0)
  expect_true(all(vapply(safe, function(operation) isTRUE(operation$safe_read), logical(1))))
})

test_that("unsafe provider operations require explicit authorization before network", {
  unsafe <- Filter(function(operation) !isTRUE(operation$safe_read), hdp_operations())
  expect_gt(length(unsafe), 0)
  operation <- unsafe[[1]]

  optional_unsafe <- Filter(
    function(candidate) {
      parameters <- candidate$parameters
      !length(Filter(function(parameter) {
        required <- parameter$required
        if (is.null(required) || !length(required)) required <- ""
        tolower(trimws(as.character(required))) %in%
          c("oui", "yes", "true", "1", "required", "obligatoire")
      }, parameters))
    },
    unsafe
  )
  if (length(optional_unsafe)) operation <- optional_unsafe[[1]]

  expect_error(
    hdp_request(operation$id, params = list()),
    "Operation write/administration blocked",
    fixed = TRUE
  )
})
