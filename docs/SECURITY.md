# Sécurité et confidentialité

## Périmètre

HDP 2.3.1 est une application locale mono-utilisateur. Elle n'a ni authentification, ni TLS local, ni séparation des rôles. Ne publiez pas son port sur le réseau et ne l'exposez pas à Internet.

## Protections présentes

- liaison de l'API à `127.0.0.1` uniquement ;
- aucun port PostgreSQL publié sur Windows ;
- service R interne à Compose ;
- mot de passe PostgreSQL aléatoire conservé dans `.env` ;
- empreintes SHA-256 des JSON et ressources ;
- noms de fichiers neutralisés et chemins confinés sous `data/` ;
- téléchargements HTTP(S) seulement, sans identifiants intégrés ;
- résolution DNS et refus des adresses privées, locales, réservées ou non globales à chaque URL et redirection ;
- limite de taille contrôlée avec `Content-Length` puis pendant le flux ;
- écriture temporaire `.part` et renommage après réussite ;
- aucun moteur d'exécution des scripts stockés ;
- jeton GitHub lu depuis l'environnement, jamais retourné par l'API ni enregistré dans les paramètres de projet ;
- dépôt GitHub privé par défaut et création précédée d'une confirmation côté interface ;
- aucune saisie libre d'identifiant HDX dans le module géographique ; filtre strict sur série COD-AB officielle, niveau COD et code ISO3 M49 ;
- suppressions de ressources confirmées dans l'interface et provenance conservée.

## Limites connues

- absence d'audit de sécurité indépendant ;
- HTTP local et données en clair sur le disque ;
- pas de chiffrement applicatif ni rotation automatique des secrets ;
- pas d'antivirus ou d'analyse du contenu téléchargé ;
- le filtrage réseau réduit le risque SSRF mais ne remplace pas une isolation réseau ;
- dépendance aux métadonnées, licences, quotas et disponibilités des sources ;
- un marquage COD officiel réduit le périmètre mais ne remplace pas l'évaluation de la qualité ou de l'adéquation d'un jeu ;
- installateur non signé par certificat d'éditeur.

## Fichiers sensibles

`%USERPROFILE%\HumanitarianDataPlatform\.env` contient le secret PostgreSQL, éventuellement l'appname ReliefWeb et `GITHUB_TOKEN`. Ne publiez jamais ce fichier. Utilisez un jeton à droits minimaux, limitez les organisations accessibles et révoquez-le lorsqu'il n'est plus nécessaire.

Le diagnostic `HDP_Diagnostic_v2.3.1.cmd` n'affiche que `HDP_PORT` depuis `.env` : ni le jeton GitHub, ni le mot de passe PostgreSQL, ni l'appname ReliefWeb. Relisez néanmoins tout journal avant de le partager : il peut contenir le nom de la machine, l'utilisateur, des chemins ou des informations Docker.

## Données humanitaires

N'utilisez pas HDP pour des données personnelles ou confidentielles sans évaluation adaptée. Les mots-clés sont transmis à la source choisie. ReliefWeb peut associer les appels à l'appname.

## Empreinte et signature

SHA-256 détecte une modification par rapport à une valeur attendue ; il ne prouve ni l'identité de l'éditeur, ni l'exactitude des données. Vérifiez les fichiers `.sha256` obtenus via un canal de confiance.

## Licence

Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé jusqu'au choix d'une licence et à la vérification des droits de redistribution des composants.
