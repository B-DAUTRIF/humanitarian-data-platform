test_that("catalog exposes ten sources", { expect_length(hdp_sources(),10) })
test_that("catalog exposes all operations", { expect_equal(length(hdp_operations()),440) })
