# Sécurité et confidentialité

## Périmètre

HDP 3.0.0 reste une application locale mono-utilisateur. Elle n'a ni authentification, ni TLS local, ni séparation des rôles. Ne publiez pas son port sur le réseau et ne l'exposez pas à Internet.

## Protections présentes

- liaison de l'API à `127.0.0.1` uniquement ;
- aucun port PostgreSQL publié sur Windows ;
- service R interne à Compose ; runners Python/R avec `network_mode: none` ;
- passerelle GitHub liée à `127.0.0.1`, conteneur non privilégié et en lecture
  seule, écritures désactivées par défaut ;
- mot de passe PostgreSQL aléatoire conservé dans `.env` ;
- empreintes SHA-256 des JSON et ressources ;
- noms de fichiers neutralisés et chemins confinés sous `data/` ;
- téléchargements HTTP(S) seulement, sans identifiants intégrés ;
- résolution DNS et refus des adresses privées, locales, réservées ou non globales à chaque URL et redirection ;
- limite de taille contrôlée avec `Content-Length` puis pendant le flux ;
- écriture temporaire `.part` et renommage après réussite ;
- exécution limitée à Python/R, versions immuables, appel direct sans shell,
  conteneurs non privilégiés et en lecture seule, limites de temps, processus,
  CPU, mémoire, fichiers et sortie ;
- toute activation réseau ou allowlist d'un job est refusée ;
- parseur RSS borné et durci contre DTD/entités, redirections limitées aux hôtes du registre ;
- Leaflet servi localement ; fond OSM désactivé jusqu'à une action explicite ;
- jeton GitHub lu depuis l'environnement, jamais retourné par l'API ni enregistré dans les paramètres de projet ;
- passerelle GitHub limitée à des routes codées en dur : elle n'accepte ni URL
  arbitraire, ni méthode libre, ni retransmission de l'en-tête Authorization ;
- dépôt GitHub privé par défaut et création précédée d'une confirmation côté interface ;
- aucune saisie libre d'identifiant HDX dans le module géographique ; filtres stricts sur `cod-ab-<iso3>`/`cod-ps-<iso3>`, les séries officielles et l'unique groupe ISO3 M49 ;
- COD-CS désactivé lorsque le registre vérifié est vide et COD-HP impossible à sélectionner ;
- absence d'une famille traitée atomiquement, sans téléchargement silencieux d'un sous-ensemble ;
- suppressions de ressources confirmées dans l'interface et provenance conservée.

## Limites connues

- absence d'audit de sécurité indépendant ;
- HTTP local et données en clair sur le disque ;
- pas de chiffrement applicatif ni rotation automatique des secrets ;
- pas d'antivirus ou d'analyse du contenu téléchargé ;
- le filtrage réseau réduit le risque SSRF mais ne remplace pas une isolation réseau ;
- dépendance aux métadonnées, licences, quotas et disponibilités des sources ;
- les connecteurs filtrant un catalogue distant peuvent transférer une réponse
  volumineuse même lorsque peu de résultats sont affichés ;
- un marquage COD officiel réduit le périmètre mais ne remplace pas l'évaluation de la qualité ou de l'adéquation d'un jeu ;
- installateur non signé par certificat d'éditeur.
- les runners partagent un spool par langage et ne sont pas une sandbox
  multi-tenant : n'exécutez que des scripts locaux de confiance ;
- activer le fond OpenStreetMap communique les requêtes de tuiles au service
  distant et impose le respect de sa politique d'utilisation ;

## Fichiers sensibles

`%USERPROFILE%\HumanitarianDataPlatform\.env` contient le secret PostgreSQL, éventuellement l'appname ReliefWeb et `GITHUB_TOKEN`. Ne publiez jamais ce fichier. Préférez un jeton finement granulé limité aux dépôts et organisations requis. La création de dépôt exige la permission de dépôt **Administration: write** ; n'accordez pas de droits de contenu supplémentaires tant qu'aucune publication n'est prévue et révoquez le jeton lorsqu'il n'est plus nécessaire.

Le diagnostic `HDP_Diagnostic_v3.0.0.cmd` n'affiche que `HDP_PORT` depuis `.env` : ni le jeton GitHub, ni le mot de passe PostgreSQL, ni l'appname ReliefWeb. Relisez néanmoins tout journal avant de le partager : il peut contenir le nom de la machine, l'utilisateur, des chemins ou des informations Docker.

## Données humanitaires

N'utilisez pas HDP pour des données personnelles ou confidentielles sans évaluation adaptée. Les mots-clés sont transmis à la source choisie lorsqu'elle permet un filtrage distant ; les autres connecteurs téléchargent un catalogue puis filtrent localement. ReliefWeb peut associer les appels à l'appname.

## Empreinte et signature

SHA-256 détecte une modification par rapport à une valeur attendue ; il ne prouve ni l'identité de l'éditeur, ni l'exactitude des données. Vérifiez les fichiers `.sha256` obtenus via un canal de confiance.

## Licence

Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé jusqu'au choix d'une licence et à la vérification des droits de redistribution des composants.
