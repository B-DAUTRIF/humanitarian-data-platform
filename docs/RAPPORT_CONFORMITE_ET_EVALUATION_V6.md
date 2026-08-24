# HDP 6.0.0-dev — conformité aux demandes et évaluation actuelle

Date d'évaluation : 24 août 2026  
Base : archive complète 5.0.2, reprise locale V6 et jalon automatisé du dépôt.

## Conclusion de conformité

Toutes les demandes du prompt de mises à jour ne sont **pas** exécutées. Le
socle V6 est un développement avancé : modèles de données, routes, protections
et plusieurs parcours d'interface existent, mais l'exhaustivité des connecteurs,
l'exécution réseau des travaux de données, la réception réseau des mails et
plusieurs recettes de plateforme restent ouvertes. La compilation de l'EXE
prouve seulement que le code Win32 produit un PE32+ ; elle ne remplace pas une
installation réelle.

Les statuts employés sont :

- **Réalisé** : code et contrôles locaux correspondants présents ;
- **Partiel** : un socle existe mais le parcours demandé n'est pas complet ;
- **Non réalisé** : fonction absente ou arbitrage empêchant l'implémentation ;
- **Non qualifié** : code présent, mais recette de la plateforme cible absente.

## Matrice des demandes

| Demande | Statut | Preuve actuelle | Reste à faire |
|---|---|---|---|
| Refonte en plugin SPIP avec site équivalent | Partiel / non qualifié | passerelle `hdp-spip/1.0`, brouillons approuvés manuellement, plugin SPIP 4.2–4.4 | recette PHP/SPIP, comptes visiteurs, déploiement Internet, équivalence écran par écran |
| Règles combinant ET et OU | Réalisé pour le moteur | arbre strict imbriqué, simulation, versionnement, tests AND/OR | constructeur visuel complet et migration des anciennes règles plates |
| Corrélations entre événements | Réalisé pour le moteur | comptage, séquence, absence, variation/tendance fixe ou glissante | essais de charge et scénarios métier représentatifs |
| Actions automatiques contrôlées | Partiel avancé / travailleurs internes vérifiés | travailleur d'actions, travaux de données et vue opérateur vérifiés sur PostgreSQL 16 ; décisions, tentatives, brouillons et résultats par source ; 267/267 tests distants | qualifier les appels connecteurs réels et les exécuteurs externes séparés |
| Règles globales héritées/surchargeables | Réalisé | versions proposées, adoption/rejet, surcharge/restauration par projet | recette multi-projets et ergonomie de comparaison des versions |
| Catalogue central de toutes les métadonnées | Partiel | schéma V6, brut immuable, normalisation, lignée, confiance, dérive | peupler et vérifier les inventaires officiels de toutes les sources |
| Tous les endpoints officiels et tous leurs paramètres | Partiel | import OpenAPI 3/Swagger 2 et activation progressive | contrats officiels complets des dix sources, champs observés et preuves datées |
| Socle commun de toutes les sources | Partiel | matrice de capacités et équivalents à la demande | adaptateurs `discover` à `provenance` complets pour chaque source |
| Équivalents en cache | Partiel | stockage adressé par contenu, publication atomique, revalidation et politique projet | JSON/CSV/Parquet complet, géographies/GeoPackage, concurrence et reprise |
| Politique `stale_if_error` par projet | Réalisé pour le modèle et l'arbitrage d'interface | politique unique, revalidation ETag/Last-Modified et recommandation fréquence × 3 plafonnée à sept jours | recette de concurrence/reprise ; les projets manuels ne changent qu'après enregistrement opérateur |
| Liste exhaustive de veille sanitaire mondiale | Partiel | registre de 15 flux officiels et cycle candidat/aperçu/approbation/abonnement | recherche officielle mondiale exhaustive, vérification en direct, flux morts/doublons |
| Module d'ajout de flux RSS | Réalisé | validation sûre, aperçu, approbation, suspension et rattachement projet | tests réseau réels et planificateur générique d'exploitation |
| Installation, raccourci et désinstallation | Réalisé et compilé / non qualifié | Shell Link COM natif ; désinstallation marquée, fichiers exacts, `compose down` sans volumes, données et tiers conservés ; MSVC strict et 270/270 tests distants | recette Windows avec chemins Unicode/espaces, Docker arrêté, cible de raccourci étrangère et reprise après échec |
| Sauvegarde globale SQL | Réalisé en base temporaire / cible non qualifiée | `pg_dump`, prévalidation, confirmation, transaction, collision refusée et suppression ; 241/241 tests PostgreSQL 16 | requalifier sur le déploiement cible |
| Sauvegarde par projet | Réalisé en base temporaire / cible non qualifiée | fermeture transitive propriété/dépendance, fichier confiné adressé par contenu, import topologique, collision refusée ; 247/247 tests PostgreSQL 16 | requalifier sur un projet représentatif complet dans le déploiement cible |
| Sauvegarde des signaux | Réalisé en base temporaire / portée à étendre | projet et règles inclus, neuf tables, tri des dépendances, transaction et collision refusée ; 244/244 tests PostgreSQL 16 | ajouter période et portée globale |
| Champs de recherche propres aux sources | Partiel | paramètres contractuels, types et valeurs contraintes exposables | générateur uniforme de formulaires pour tous les contrats peuplés |
| Configuration et paramètres API visibles par source | Partiel | liens Portail/Documentation/API/configuration et détail contractuel | exhaustive seulement après inventaires officiels complets |
| Paramétrages sous chaque source, global/projet | Réalisé | bouton par encart et deux portées conservées | recette ergonomique complète |
| Chronologie globale et projet | Partiel | vues séparées et plusieurs événements V6 audités | couvrir migrations, contrats, tables globales et chaque exécution projet |
| Ouvrir le dossier contenant | Partiel | exploration confinée distante sans divulgation du chemin | action native locale, liens symboliques, droits et fichiers supprimés |
| Lecture/réception de mails | Partiel | import manuel EML public, redaction, stockage confiné, rattachement et règle | choisir IMAP OAuth2, mot de passe d'application ou passerelle ; antimalware et polling |
| Runners Python/R avec réseau réellement coupé | Réalisé comme contrainte | `network_mode:none` et état d'indisponibilité explicite | proxy d'egress dédié si des accès sortants doivent être autorisés |
| Diagnostic complet après chaque lot | Réalisé localement, partiel globalement | jalon reproductible Python/SQL/JS/OpenAPI/C runner | Docker, Windows installé, PHP/SPIP, restaurations et connecteurs réels |
| Archive et EXE à la demande seulement | Réalisé comme procédure | script de packaging et workflow Windows versionnés | signature Authenticode et qualification finale distinctes |

## Évaluation technique et fonctionnelle

Cette notation est une appréciation d'ingénierie sur cinq niveaux, fondée sur
les preuves disponibles ; ce n'est ni une certification ni une mesure de charge.

| Axe | Niveau | Appréciation |
|---|---:|---|
| Architecture et traçabilité | 4/5 | structure modulaire cohérente, migrations et états explicites ; plusieurs travailleurs restent à livrer |
| Couverture fonctionnelle V6 | 3/5 | la plupart des concepts ont un modèle et une API ; plusieurs parcours ne sont pas bout en bout |
| Qualité automatisée locale | 4/5 | suite large, AST, SQL, JavaScript, OpenAPI et runner C ; peu d'intégration réelle |
| Sécurité de conception | 3,5/5 | passkeys, SSRF, confinement, sessions hachées et validations ; recettes Internet/antimalware/audit absentes |
| Exploitation et déploiement | 2/5 | installateurs et Compose préparés ; Windows installé, Docker, SPIP, sauvegarde-restauration et supervision non qualifiés |
| Maturité métier des sources | 2/5 | infrastructure de catalogue solide ; exhaustivité mondiale et validation sanitaire encore incomplètes |

**Niveau global actuel : préversion technique avancée, environ 3/5.** Elle est
adaptée à la poursuite du développement et aux recettes contrôlées, pas à une
mise en production Internet ni à une veille sanitaire déclarée exhaustive.

## Risques prioritaires

1. L'absence d'inventaires officiels complets peut donner une interface riche
   sans garantir que tous les paramètres et champs des sources sont disponibles.
2. Les deux travailleurs internes sont vérifiés sur PostgreSQL 16, mais les
   appels connecteurs réels, leurs quotas et l'annulation d'un transfert HTTP
   en cours restent non qualifiés.
3. Les chemins global, signaux et projet sont prouvés en base temporaire ; une
   recette sur données représentatives dans le déploiement cible reste nécessaire
   avant tout usage critique.
4. Le plugin SPIP et WebAuthn doivent être testés derrière le reverse proxy HTTPS
   réel, avec les comptes nominatifs et la révocation.
5. Les mails et pièces jointes ne doivent pas être automatisés sans choix du
   protocole, isolation de l'analyse et moteur antimalware.

## Prochains jalons recommandés

1. Qualifier l'EXE sur Windows 10/11 avec Docker Desktop et une mise à niveau
   depuis 5.0.2, puis vérifier le raccourci et les journaux.
2. Requalifier les sauvegardes avec un projet représentatif contenant ressources,
   cache, mails et cartographie dans le déploiement Windows/Docker cible.
3. Peupler source par source les inventaires officiels, avec preuves datées et
   tests de contrat, avant d'annoncer une exhaustivité.
4. Exécuter les `automated_data_jobs` avec les connecteurs réels, leurs quotas,
   reprises, annulations et résultats partiels, sans ouvrir l'egress aux scripts.
5. Choisir le protocole réseau de réception de mails et le fournisseur cible.
6. Déployer un environnement SPIP/HTTPS de recette et vérifier l'équivalence
   fonctionnelle, les comptes visiteurs et la publication manuelle.
