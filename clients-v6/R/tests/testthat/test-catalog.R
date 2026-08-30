test_that("catalog exposes ten stable source slugs", {
  expect_length(hdp_sources(), 10)
  expect_setequal(
    hdp_sources(),
    c("hdx", "reliefweb", "who-gho", "world-bank-health", "unicef-sdmx", "un-sdg", "dhs", "hdx-hapi", "unhcr", "gdacs")
  )
})

test_that("provider catalog is versioned, substantial and internally unique", {
  ops <- hdp_operations()
  # The global HDP inventory has 196 operations: ten are the canonical HDP
  # source-registry configuration operations and 186 are executable provider
  # operations shipped in the standalone R/Python source clients.
  expect_equal(length(ops), 186)
  ids <- vapply(ops, function(x) x$id, character(1))
  expect_length(unique(ids), length(ids))
  expect_true(all(nzchar(ids)))
  expect_true(all(vapply(ops, function(x) nzchar(x$source_slug), logical(1))))
  expect_setequal(unique(vapply(ops, function(x) x$source_slug, character(1))), hdp_sources())
})

test_that("source filters return only the requested connector", {
  for (source in hdp_sources()) {
    ops <- hdp_operations(source)
    expect_gt(length(ops), 0)
    expect_true(all(vapply(ops, function(x) identical(x$source_slug, source), logical(1))))
  }
})

test_that("preview constructs a safe HTTPS request from catalog metadata", {
  ops <- hdp_operations(safe_only=TRUE)
  usable <- Filter(function(op) {
    params <- op$parameters
    !length(Filter(function(p) {
      required_value <- if (is.null(p$required)) "" else p$required
      location_value <- if (is.null(p$location)) "" else p$location
      default_value <- p$default
      default_missing <- is.null(default_value) || !length(default_value) || !any(nzchar(as.character(default_value)))
      required <- any(tolower(trimws(as.character(required_value))) %in% c("oui", "yes", "true", "1", "required", "obligatoire"))
      required && default_missing && any(grepl("path", tolower(as.character(location_value))))
    }, params))
  }, ops)
  expect_gt(length(usable), 0)
  preview <- hdp_preview(usable[[1]]$id)
  expect_true(preview$method %in% unlist(usable[[1]]$methods))
  expect_match(preview$url, "^https://")
  expect_true(is.list(preview$query))
  expect_true(is.list(preview$headers))
})

test_that("unknown operations and forbidden methods fail explicitly", {
  expect_error(hdp_preview("operation-that-does-not-exist"), "Unknown operation_id")
  op <- hdp_operations()[[1]]
  forbidden <- setdiff(c("GET", "POST", "PUT", "PATCH", "DELETE"), unlist(op$methods))
  if (length(forbidden)) {
    expect_error(hdp_preview(op$id, method=forbidden[[1]]), "Method not allowed")
  }
})

test_that("exports preserve usable tabular data and provenance", {
  response <- structure(list(
    source="WHO GHO",
    operation_id="test-operation",
    method="GET",
    url="https://example.invalid/data",
    status_code=200,
    elapsed_seconds=0.1,
    data=list(results=list(list(id="a", cases=2), list(id="b", cases=3)))
  ), class="hdp_response")
  json_path <- tempfile(fileext=".json")
  csv_path <- tempfile(fileext=".csv")
  xlsx_path <- tempfile(fileext=".xlsx")
  on.exit(unlink(c(json_path, csv_path, xlsx_path)), add=TRUE)
  expect_identical(hdp_export_json(response, json_path), json_path)
  expect_identical(hdp_export_csv(response, csv_path), csv_path)
  expect_identical(hdp_export_xlsx(response, xlsx_path), xlsx_path)
  expect_true(file.info(json_path)$size > 0)
  expect_true(file.info(csv_path)$size > 0)
  expect_true(file.info(xlsx_path)$size > 0)
  csv <- utils::read.csv(csv_path, stringsAsFactors=FALSE)
  expect_equal(nrow(csv), 2)
  expect_named(csv, c("id", "cases"))
  expect_equal(as.numeric(csv$cases), c(2, 3))
  expect_equal(sum(as.numeric(csv$cases)), 5)
})
