# Rapport de validation — Humanitarian Data Platform 3.0.0 finale

Date : 15 août 2026  
Environnement : Linux x86-64 de construction, sans Docker ni Windows

## Résultat

| Contrôle | Résultat |
|---|---|
| Compilation Python API principale et passerelle GitHub | réussi |
| Tests Python | **68/68 réussis** |
| OpenAPI API principale | **47 chemins / 63 opérations** |
| OpenAPI passerelle GitHub | **11 chemins / 12 opérations** |
| JavaScript inline de l'interface | syntaxe valide avec Node.js |
| Compose | YAML valide, 6 services attendus |
| Runner C | compilation C17 stricte réussie |
| Runner fonctionnel | succès, heartbeat et `timed_out` validés |
| Payload embarqué | **39 fichiers** reconstruits octet pour octet |
| Installateur Windows | PE32+ GUI x86-64 réel, 773 632 octets |
| Protections PE | HIGH_ENTROPY_VA, DYNAMIC_BASE, NX_COMPAT |
| Documentation | HTML valide ; PDF A4 de 36 pages, rendu inspecté |

## Installateur final

- fichier : `HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe` ;
- SHA-256 : `9018d3d17866fcd246bf2b20a17f88dc5f9bcafea9adbde50a385502b3d0bb97` ;
- sous-système : Windows GUI ;
- architecture : x86-64 ;
- version applicative : 3.0.0.

## Contrôles de sécurité

- runners Python/R sans réseau et sans invocation de shell ;
- passerelle GitHub liée à `127.0.0.1`, non privilégiée, en lecture seule au
  niveau du système de fichiers et sans capacité Linux ;
- écritures GitHub désactivées par défaut ;
- absence de `docker.sock`, `docker compose down -v`, `system()` et `popen()`
  dans les contrats concernés ;
- secrets exclus des réponses et de la documentation de livraison.

## Limites explicites

Docker n'est pas installé dans l'environnement de construction. Les services
Compose/PostGIS n'ont donc pas fait l'objet d'une recette d'intégration ici.
Windows n'est pas disponible non plus : l'installation, la mise à niveau réelle
depuis 2.5.0, Docker Desktop/WSL 2, les raccourcis et l'ouverture du navigateur
doivent encore être vérifiés sur un poste Windows 10/11 x64. Aucun de ces essais
n'est présenté comme réussi.

## Conclusion

Tous les contrôles réalisables dans l'environnement de construction sont
réussis. La version 3.0.0 peut être figée et publiée avec la réserve de recette
Windows/Docker clairement documentée.
