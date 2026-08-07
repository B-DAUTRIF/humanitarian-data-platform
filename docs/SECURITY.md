# Sécurité et confidentialité

## Protections présentes

- l'API est publiée uniquement sur `127.0.0.1` ;
- PostgreSQL n'a aucun port publié sur Windows ;
- R reste interne au réseau Docker Compose ;
- le mot de passe PostgreSQL est généré aléatoirement ;
- chaque acquisition archivée reçoit une empreinte SHA-256 ;
- les liens externes de l'interface utilisent `rel=noopener`.

## Limites connues

- aucune authentification ni séparation des utilisateurs ;
- HTTP local sans TLS ;
- `.env` et les JSON sont stockés en clair sur le disque Windows ;
- aucun chiffrement applicatif, audit de sécurité ou mécanisme de rotation des secrets ;
- aucune politique intégrée de mise à jour automatique ;
- l'accès à Docker confère des privilèges importants sur la machine ;
- la version 1.5 est un MVP local et ne doit pas être exposée directement sur Internet.

## Fichiers sensibles

Le fichier `%USERPROFILE%\HumanitarianDataPlatform\.env` contient le mot de passe PostgreSQL et éventuellement l'appname ReliefWeb. Il doit rester secret.

Ne placez jamais dans un ticket, un dépôt ou un journal partagé :

- le contenu complet de `.env` ;
- un mot de passe, jeton ou clé d'API ;
- un journal système non relu contenant des noms d'utilisateur, noms de machine, adresses ou chemins personnels ;
- des données humanitaires personnelles ou confidentielles.

Le script `HDP_Diagnostic_v1.5.cmd` n'affiche volontairement que `HDP_PORT` dans `.env`. Le journal Windows de référence fourni pendant le diagnostic n'est pas inclus dans ce dépôt.

## Données envoyées aux sources

Les mots-clés de recherche sont envoyés à ReliefWeb ou HDX. ReliefWeb peut associer les appels à l'appname. L'utilisateur reste responsable du respect des quotas, licences, conditions d'utilisation et droits des producteurs.

## Empreinte et signature

SHA-256 détecte une modification du fichier contrôlé. Il ne constitue pas une signature de l'éditeur ni une preuve de l'exactitude des données distantes.

L'installateur v1.5 n'est pas signé par un certificat d'éditeur. Vérifiez son empreinte avant l'exécution :

```text
1e77042dbbd7a7d400c690076bc61e3c7191c5e928cdb016a39292af2a362470
```

## Publication du dépôt

La version 1.5 ne contient aucune licence explicite. Le dépôt doit rester privé jusqu'au choix d'une licence et à la vérification des droits de redistribution de chaque composant livré.
