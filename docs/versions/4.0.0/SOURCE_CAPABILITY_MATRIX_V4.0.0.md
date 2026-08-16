# Matrice des sources - HDP 4.0.0

Vérification documentaire : 15 août 2026. `Natif` signifie que le critère est
traduit vers l’API. `Local` signifie qu’il est appliqué aux métadonnées
normalisées après la réponse. Les limites et modalités de réutilisation restent
celles de chaque producteur.

| Source | État HDP | Mots-clés | Dates | Localisation | Ressource | Fréquence affichée |
|---|---|---|---|---|---|---|
| HDX/CKAN | actif | natif | local | local | fichiers publiés | métadonnée du jeu |
| ReliefWeb | actif, appname | natif | local | local | pièces jointes référencées | non publiée |
| WHO GHO | actif | natif catalogue | local | local | JSON par indicateur | variable |
| World Bank Health | actif | local catalogue | local | local | archive CSV | variable |
| UNICEF SDMX | actif | local flux | local | local | CSV du flux | variable |
| UN SDG | actif | local indicateurs | local | local | série JSON | variable |
| DHS | actif, agrégats | local indicateurs | local | local | données JSON | enquêtes |
| HDX HAPI v2 | expérimental, identifiant | local | sous-domaine/local | code natif | réponse brute | hebdomadaire à annuelle |
| UNHCR | actif | local | année native | origine/asile natifs | extraction JSON | annuelle |
| GDACS | actif | local | natif | local | GeoJSON | quasi temps réel |

Les paramètres propres à chaque source sont publiés par JSON Schema et rendus
directement sous la source sélectionnée. Un critère commun non natif n’est
jamais présenté comme natif : son mode reste dans le contrat et la provenance.

## Portails référencés, non automatisés

WHO Disease Outbreak News, IOM DTM, WHO Mortality, GLASS, FluNet/FluID, Global
Health Estimates, UNAIDS, IHME GHDx, UNICEF MICS, UN WPP, Global.health,
WorldPop et Our World in Data sont référencés sans scraping ni contournement
d’accès.

## Références officielles

- HDX HAPI : https://hapi.humdata.org/ et https://hdx-hapi.readthedocs.io/
- UNHCR : https://api.unhcr.org/docs/refugee-statistics.html
- GDACS : https://www.gdacs.org/gdacsapi/swagger/index.html
- IOM DTM : https://dtm.iom.int/data-and-analysis
- WHO GHO : https://www.who.int/data/gho/info/gho-odata-api
- WorldPop API : https://api.worldpop.org/v2/

