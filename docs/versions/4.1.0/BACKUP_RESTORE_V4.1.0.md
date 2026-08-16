# Sauvegarde et restauration - HDP 4.1.0

## Sauvegarder

Exécuter `backup-hdp.ps1` depuis le dossier installé. Le script exporte
PostgreSQL, `data/`, `.env` et un manifeste `HDP_BACKUP_VERSION=4.1.0`. La
sauvegarde contient potentiellement des secrets et ne doit pas être publiée.

## Restaurer

1. Arrêter les traitements et conserver le dossier courant.
2. Exécuter `restore-hdp.ps1` avec la sauvegarde choisie.
3. Saisir exactement `RESTORE-HDP` lorsque le script le demande.
4. Contrôler la santé de l'API et les réglages des dix sources.

Le script accepte les sauvegardes 4.0.0 et 4.1.0, crée d'abord une sauvegarde de
sécurité, puis renomme les anciens `.env` et `data/` au lieu de les supprimer.
Ne jamais utiliser `docker compose down -v` pour une opération de maintenance
normale : cette commande supprime le volume PostgreSQL.
