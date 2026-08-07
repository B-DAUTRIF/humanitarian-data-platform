#* État du service analytique R
#* @get /health
function() {
  list(status = "ok", language = "R", version = as.character(getRversion()))
}

#* Résumé descriptif d'un vecteur numérique
#* @param values Valeurs séparées par des virgules
#* @get /summary
function(values = "") {
  x <- suppressWarnings(as.numeric(strsplit(values, ",", fixed = TRUE)[[1]]))
  x <- x[is.finite(x)]
  if (length(x) == 0) {
    return(list(n = 0, mean = NULL, sd = NULL, median = NULL))
  }
  list(
    n = length(x),
    mean = mean(x),
    sd = if (length(x) > 1) sd(x) else NULL,
    median = median(x),
    minimum = min(x),
    maximum = max(x)
  )
}
