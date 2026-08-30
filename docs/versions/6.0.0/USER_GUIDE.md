# HDP V6.0.0 — Guide utilisateur

## Installation

L'installateur Windows V6 déploie le payload local, conserve la configuration existante lors d'une mise à niveau, détecte les dépendances et peut proposer l'installation explicite de Docker Desktop, Git et Visual Studio Code via winget. Le module R reste optionnel. Après démarrage des services, l'interface est ouverte dans le navigateur local.

## Navigation

- **Recherche** : recherche fédérée multi-source.
- **Data Grid & SIGNALS** : exploration et signaux.
- **Sources sanitaires** : catalogue des sources.
- **Paramètres des sources** : configuration individualisée par source.
- **Inventaire API** : totalité des paramètres catalogués, recherche et filtre par source.
- **Projets & préférences** : réglages par projet et intégrations.
- **Données locales** : bibliothèque, imports et ressources locales.
- **Flux RSS** : sources RSS configurées.
- **Chronologie** : événements et activités planifiées.
- **Carte** : données géographiques locales.
- **Scripts / Notebooks** : traitements reproductibles Python/R.
- **Planifications** : exécutions récurrentes.
- **Base SQL** : espace de requêtes en lecture contrôlée.
- **USER · Technologies & code** : documentation technique et technologies.

## Inventaire API

L'inventaire est volontairement exhaustif. Un paramètre qui ne doit pas être édité est conservé comme information visible et identifié en lecture seule. Les paramètres éditables sont associés à un contrôle UI recommandé (texte, nombre, liste, sélection multiple, date, booléen, etc.) lorsque le catalogue le prévoit.

La documentation générée `API_INVENTORY.md` et `API_INVENTORY.csv` contient la même base complète, groupée par source.
