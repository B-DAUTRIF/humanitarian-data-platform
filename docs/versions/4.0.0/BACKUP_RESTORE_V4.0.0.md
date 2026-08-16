# Sauvegarde et restauration - HDP 4.0.0

## Sauvegarder

Depuis PowerShell dans le dossier HDP :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\backup-hdp.ps1
```

Le script exporte PostgreSQL, copie `data/` et `.env`, calcule les empreintes et
crée une archive datée dans `backups/`. Elle contient les secrets de `.env` :
ne la publiez pas, chiffrez son stockage et limitez-en l’accès.

## Restaurer

La restauration remplace volontairement la base et les données courantes. Elle
exige une confirmation, commence par une nouvelle sauvegarde et renomme les
données courantes au lieu de les supprimer.

```powershell
.\restore-hdp.ps1 -Archive .\backups\HDP_backup_YYYYMMDDTHHMMSSZ.zip -Confirmation RESTORE-HDP
```

Après restauration, vérifiez `/api/health`, le projet, la bibliothèque, un
SHA-256, les couches et une requête SQL. Conservez `data.before-restore-*` et
`.env.before-restore-*` jusqu’à validation complète.

Les scripts sont livrés, mais une restauration réelle sur Windows/Docker et un
jeu représentatif reste une recette externe à consigner.

