# Index de la documentation HDP

La documentation est classée par version. Les fichiers de `main` décrivent la livraison installable qualifiée **5.0.2** ; le développement **5.2** se poursuit sur `develop/5.2`.

## Documentation technique par version

| Version | Statut | Dossier |
|---|---|---|
| 2.3.0 à 2.4.0 | distributions et prompts historiques | [`dist/`](../dist/README.md) ; aucune seconde copie exacte |
| 2.5.0 | documentation historique | [`versions/2.5.0`](versions/2.5.0/) |
| 3.0.0 | livraison historique | [`versions/3.0.0`](versions/3.0.0/) |
| 4.0.0 | livraison historique | [`versions/4.0.0`](versions/4.0.0/) |
| 4.1.0 | état audité historique | [`versions/4.1.0`](versions/4.1.0/) |
| 5.0.0 | UML initial V5 | [`versions/5.0.0`](versions/5.0.0/) |
| 5.0.2 | dernière livraison qualifiée | [`versions/5.0.2`](versions/5.0.2/) |

## Traçabilité et gouvernance

- [Traçabilité](traceability/README.md)
- [Structure du dépôt](governance/REPOSITORY_STRUCTURE.md)
- [Politique de publication](governance/RELEASE_POLICY.md)
- [Audit des doublons du 16 août 2026](governance/DUPLICATE_AUDIT_2026-08-16.md)

Les distributions binaires et archives complètes sont conservées séparément sous [`dist/`](../dist/README.md). Lorsqu’un document est déjà présent à l’identique dans une distribution non compressée, `dist/<version>/` reste son emplacement canonique afin d’éviter une seconde copie navigable.
