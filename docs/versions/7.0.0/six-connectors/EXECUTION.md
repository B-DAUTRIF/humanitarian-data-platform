# HDP V7 — campagne dev_connecteurs sur six fournisseurs

Périmètre : DHS, GDACS, UN SDG, UNHCR, UNICEF SDMX et WHO GHO.

Référence normative : `docs/prompts/dev_connecteurs.md`.

Cette campagne applique sans transfert de statut les phases A à J : preuves officielles, matrice endpoint/opération/paramètre, package fournisseur dédié, UI Simple/Avancé/Expert, délégation du routeur sémantique vers le service de référence, clients Python/R, nomenclatures vérifiées, 10 cycles déterministes par fonctionnalité, sentinelles live, régression HDP complète, documentation et évaluation métier.

Règle de qualification : un contrôle non exécuté reste `NOT TESTED`; une erreur fournisseur reste une erreur; une réponse bornée vide n'est jamais une preuve d'absence globale.

État initial : les six sources disposent d'entrées `source_registry` et d'un runtime générique. Elles ne sont pas requalifiées par cette campagne tant que les nouveaux services spécialisés, matrices, tests et preuves live du head exact n'ont pas été inspectés.
