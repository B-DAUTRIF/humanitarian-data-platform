# Architecture HDP V6.0.0

## Périmètre

Humanitarian Data Platform V6 est une application locale orientée données humanitaires et sanitaires. L'architecture de référence associe une API FastAPI, PostgreSQL/PostGIS, une interface web servie par l'API, des traitements Python et R, des runners isolés, un installateur Windows natif et Docker Compose pour l'orchestration locale.

## Vue logique

```text
Utilisateur Windows
    |
    +-- Installateur natif HDP 6.0.0
    |      +-- déploie le payload
    |      +-- prépare la configuration locale
    |      +-- orchestre Docker Compose
    |      +-- crée le raccourci « Humanitarian Data Platform.lnk »
    |
    +-- Navigateur local : http://localhost:8080
           |
           +-- FastAPI / API HDP V6
           |      +-- projets et bibliothèque
           |      +-- registre et inventaire des sources
           |      +-- recherche fédérée et acquisitions
           |      +-- provenance / intégrité
           |      +-- règles, signaux, actions et timeline
           |      +-- jobs planifiés
           |      +-- sauvegardes / restauration
           |      +-- passkey / sécurité
           |      +-- mail / SPIP / GitHub
           |      +-- OpenAPI
           |
           +-- PostgreSQL/PostGIS
           |
           +-- spool d'exécution
                  +-- runner Python sans réseau
                  +-- runner R sans réseau

Sources externes documentées
    +-- HDX
    +-- ReliefWeb
    +-- WHO GHO
    +-- World Bank Health
    +-- UNICEF SDMX
    +-- UN SDG
    +-- DHS
    +-- HDX HAPI
    +-- UNHCR
    +-- GDACS
```

## Contrats des sources

Le registre V6 expose dix connecteurs. Les critères communs sont normalisés dans HDP puis transformés par chaque adaptateur. L'inventaire API conserve les paramètres fournisseurs et leur provenance documentaire. Un paramètre fournisseur n'est présenté comme directement modifiable que lorsqu'il correspond à un champ canonique effectivement câblé ; les autres paramètres restent visibles comme informations ou paramètres gérés par l'adaptateur.

## Données et persistance

PostgreSQL/PostGIS est la persistance transactionnelle. Les migrations sont versionnées et non destructives pour le parcours de mise à niveau. Les fichiers acquis ou importés sont conservés dans la bibliothèque locale et associés aux métadonnées de provenance. Les opérations sensibles de cache et de publication utilisent des mécanismes d'écriture atomique et d'identification par empreinte lorsque le module concerné le prévoit.

## Exécution scientifique

Les scripts utilisateur sont limités à Python et R. Ils transitent par un spool partagé avec des runners dédiés, sans accès réseau et avec limites de ressources. Le service R/plumber est séparé de l'API principale. Les clients Python et R accèdent aux contrats HDP, et non directement aux secrets de fournisseurs.

## Sécurité

Le déploiement local lie l'API à l'interface de loopback. Les conteneurs applicatifs abandonnent les capacités inutiles, utilisent un système de fichiers en lecture seule lorsque possible et des tmpfs bornés. L'authentification opérateur, la protection CSRF, la validation des hôtes externes, les contrôles d'URL et l'accès SQL en lecture seule constituent des frontières de sécurité distinctes. Les secrets ne doivent pas apparaître dans les journaux, prévisualisations de requêtes ou artefacts de qualification.

## Intégrations

GitHub est associé aux projets pour les opérations de synchronisation prévues par le contrat HDP. Le pont SPIP, l'ingestion mail/RSS, les sauvegardes, les actions, la timeline et les jobs automatisés sont des modules V6 distincts intégrés à l'API et à la base.

## Windows et distribution

La version finale porte l'identité `6.0.0` dans l'API, l'installateur, les ressources PE, les scripts de build, les images de runners et le packager. Le build Windows de référence utilise MSVC x64 et produit `HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0.exe`. Le packager contrôle le format PE32+ GUI x86-64 et produit l'archive complète avec manifestes et empreintes SHA-256.

## Qualification

La présence de code n'est pas une preuve de fonctionnement. La qualification V6 suit `docs/V6_FUNCTIONAL_VALIDATION_MATRIX.md`. Une porte devient `VALIDE` uniquement si son test applicable et sa preuve reproductible sont disponibles. La release n'est qualifiée que lorsque les contrôles Linux, Windows, intégration base de données et E2E métier sont verts sur le même HEAD.
