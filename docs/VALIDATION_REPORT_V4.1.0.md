# Rapport de validation - HDP 4.1.0

Date : 15 août 2026.

## Contrôles réussis

- 101 tests Python `unittest` ;
- compilation syntaxique Python ;
- deux scripts JavaScript inline analysés ;
- contrôles statiques de sécurité ;
- dix contrats globaux distincts et bornés ;
- profils techniques, liens HTTPS et exemples expurgés pour dix sources ;
- catalogue de 25 ressources, 13 catégories et 87 liens ;
- compatibilité de lecture des paramètres globaux 4.0.0 ;
- métadonnées de l'installateur alignées sur 4.1.0.
- payload embarqué de 48 fichiers reconstruit octet pour octet ;
- installateur PE32+ GUI x64, ASLR, NX et haute entropie ;
- notice PDF de 30 pages rendue et inspectée sans page vide.

## Contrôles de livraison

SHA-256 de l'installateur vérifié :
`e54d472b7a71836438252040ecef56fdc71be8c6f637f2677ce438b3341ae78f`.
Les empreintes finales des archives et leur lecture CRC sont consignées dans le
manifeste et `SHA256SUMS.txt` générés avec les livrables.

## Contrôles externes restants

- démarrage complet Docker Compose/PostGIS sur un poste cible ;
- appels directs représentatifs aux dix API, selon les identifiants disponibles ;
- recette d'installation et de mise à niveau Windows 10/11 ;
- signature Authenticode, audit indépendant et choix d'une licence.

Le périmètre local valide le code, les contrats, la documentation et la chaîne
de construction. Il ne remplace pas la disponibilité future des services tiers
ni une qualification métier des données obtenues.
