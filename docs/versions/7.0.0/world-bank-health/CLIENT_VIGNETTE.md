# World Bank Health — vignette reproductible Python / R

## Principe
Les clients spécialisés appellent HDP, pas l'API fournisseur directement. Cela préserve configuration de projet, classification des erreurs, provenance et normalisation. Les appels sémantiques restent disponibles pour la recherche multisource.

## Python
```python
from hdp_clients import HDPClient
c = HDPClient("http://localhost:8080", token="<HDP_TOKEN>")
# Recherche HDP spécialisée World Bank via les méthodes du client V7.
result = c.world_bank_observations(country="RWA", indicator="SH.MLR.INCD.P3", date="2020:2025")
```

## R
```r
library(hdpclients)
result <- hdp_world_bank_observations(
  country = "RWA",
  indicator = "SH.MLR.INCD.P3",
  date = "2020:2025",
  token = Sys.getenv("HDP_TOKEN")
)
```

## Reproductibilité
Toujours conserver : commit HDP, source World Bank, code indicateur, géographie, période, paramètres natifs, date d'exécution, URL native expurgée, statut HTTP, version/hash du vocabulaire géographique et résultat normalisé. Les identifiants d'agrégats World Bank ne doivent jamais être traités comme des ISO3 souverains.

La génération HTML/PDF de cette vignette est un objectif du build documentaire ; le Markdown est la source versionnée de référence.
