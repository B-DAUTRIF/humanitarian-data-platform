# Composants et données tiers

## Leaflet 1.9.4

Le code de rendu cartographique Leaflet 1.9.4 est embarqué sous
`api/static/vendor/leaflet`. Sa licence BSD-2-Clause complète est conservée dans
`api/static/vendor/leaflet/LICENSE`.

- Projet : <https://leafletjs.com/>
- Version : 1.9.4
- Téléchargement : paquet npm officiel `leaflet@1.9.4`

## OpenStreetMap

Aucune tuile OpenStreetMap n'est incorporée. Le fond facultatif utilise
`https://tile.openstreetmap.org/{z}/{x}/{y}.png` uniquement après activation par
l'utilisateur, avec attribution visible. La politique du service s'applique :
<https://operations.osmfoundation.org/policies/tiles/>.

## defusedxml 0.7.1

Le parseur RSS utilise `defusedxml` 0.7.1 pour renforcer le traitement XML.
Le paquet est distribué sous licence PSF :
<https://github.com/tiran/defusedxml/blob/main/LICENSE>.

## Flux RSS ReliefWeb

Le registre embarque uniquement les URL publiques officielles documentées par
ReliefWeb pour les mises à jour, catastrophes, emplois et formations. Aucun
contenu de flux n'est incorporé : <https://reliefweb.int/rss>.

## Référentiel ONU M49

Le fichier `api/app/un_m49_snapshot.json` reproduit la nomenclature publiée par la
Division de statistique des Nations Unies sous le titre *Standard country or area
codes for statistical use (M49)*.

- Source d'autorité : <https://unstats.un.org/unsd/methodology/m49/overview/>
- Instantané généré le 7 août 2026.
- Intermédiaire de génération : paquet npm `un-m49` 2.2.0,
  <https://github.com/wooorm/un-m49>.

Le paquet intermédiaire `un-m49` est distribué sous licence MIT :

> MIT License
>
> Copyright (c) 2017 Titus Wormer <tituswormer@gmail.com>
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

L'affectation des pays ou zones à des groupements ONU dans M49 est statistique et
n'implique aucune prise de position politique de HDP.

## Références OCHA pour les familles COD

Le fichier `api/app/official_cod_cs_registry.json` contient uniquement des
métadonnées de contrôle créées pour HDP. Son registre est vide dans la version
2.4.0 ; il cite la documentation OCHA afin d'expliquer pourquoi COD-CS ne peut
pas être assimilé à une série HDX canonique universelle.

- Types COD actuels et retrait de COD-HP :
  <https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/42045911/Common+Operational+Datasets+CODs>
- COD-CS, jeux spécifiques à un contexte national :
  <https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/2965897217/Country-specific+CODs+COD-CS>

Ces références n'accordent aucun droit supplémentaire sur les jeux téléchargés.
La licence et les conditions de chaque fiche HDX restent applicables.

## Catalogues sanitaires et épidémiologiques

HDP 5.0.0 contient uniquement les métadonnées descriptives, liens et adaptateurs
nécessaires à l'interrogation des services ci-dessous. Aucun jeu de données de
ces organismes n'est incorporé à l'application. Les réponses et fichiers restent
soumis aux licences, conditions, quotas et politiques d'accès de leur éditeur.

- WHO Global Health Observatory : <https://www.who.int/data/gho/info/gho-odata-api>
- World Bank Indicators API : <https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation>
- UNICEF SDMX API : <https://data.unicef.org/sdmx-api-documentation/>
- UN Global SDG API : <https://unstats.un.org/sdgapi/swagger/>
- DHS Program API : <https://api.dhsprogram.com/>
- HDX Humanitarian API : <https://hdx-hapi.readthedocs.io/>
- UNHCR Refugee Statistics API : <https://api.unhcr.org/docs/refugee-statistics.html>
- GDACS API : <https://www.gdacs.org/gdacsapi/swagger/index.html>
- IOM Displacement Tracking Matrix : <https://dtm.iom.int/data-and-analysis>
- WHO Disease Outbreak News : <https://www.who.int/emergencies/disease-outbreak-news>
- WHO Mortality Database : <https://www.who.int/data/data-collection-tools/who-mortality-database>
- WHO GLASS : <https://www.who.int/initiatives/glass>
- WHO FluNet / FluID : <https://www.who.int/tools/flunet>
- WHO Global Health Estimates : <https://www.who.int/data/global-health-estimates>
- UNAIDS AIDSinfo : <https://www.unaids.org/en/topic/data>
- IHME Global Health Data Exchange : <https://ghdx.healthdata.org/>
- UNICEF MICS : <https://mics.unicef.org/>
- UN World Population Prospects : <https://population.un.org/wpp/>
- Global.health : <https://global.health/>
- WorldPop : <https://www.worldpop.org/>
- Our World in Data : <https://ourworldindata.org/health-meta>

L'entrée Our World in Data est identifiée comme agrégateur secondaire : la
source primaire et sa licence doivent être vérifiées avant réutilisation.
