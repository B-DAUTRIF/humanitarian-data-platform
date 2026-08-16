# HDP 4.1.0 - point de reprise

## État livré

La version 4.1.0 individualise la configuration de chacun des dix connecteurs,
documente ses contraintes, ajoute une prévisualisation cURL/Python/R expurgée et
une page utilisateur de 87 liens vers le code, les technologies, logiciels
tiers, standards et sources officielles.

Le dossier de livraison est :
[Google Drive - HDP v4.1.0 - Code et livrables](https://drive.google.com/drive/folders/15rAjpoEWVnZfUzdmBaBOnO3sUeVZX7C0).

## Validation

- 101/101 tests Python réussis ;
- JavaScript inline et contrôles statiques réussis ;
- dix schémas globaux indépendants ;
- compatibilité des valeurs 4.0.0 ;
- code source, archive complète, portable, notice, empreintes et installateur
  réunis par le script de gel.

## Reprise technique

Le code principal se trouve dans `source/payload/api/`. Le registre des sources
est `app/source_registry.py`, le catalogue de liens
`app/technology_registry.py`, l'interface `static/index.html` et les tests
spécifiques `source/tests/test_v41_source_configuration.py`.

Les migrations 4.0.0 restent inchangées et idempotentes. Les secrets demeurent
dans `.env`; ne jamais déposer `.env`, `data/` ou une sauvegarde sur un espace
partagé non protégé.
