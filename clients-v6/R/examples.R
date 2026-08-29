library(HDPClientsR)
ops <- hdp_operations("HDX / CKAN", safe_only=TRUE)
search <- Filter(function(x) x$endpoint == "/api/3/action/package_search", ops)[[1]]
print(hdp_preview(search$id, list(q="cholera", rows=5)))
# resp <- hdp_request(search$id, list(q="cholera", rows=5))
# hdp_export_csv(resp, "hdx_cholera.csv")
