# Plugin SPIP HDP 1.0.0-dev

Ce plugin SPIP 4.2 à 4.4 importe exclusivement les publications publiques que
l'opérateur a approuvées manuellement dans HDP V6. Il n'a accès ni aux runners,
ni aux connecteurs, ni à PostgreSQL. Une publication retirée dans HDP devient
immédiatement non publiée lors de la synchronisation suivante.

## Configuration

1. Créer une connexion SPIP depuis HDP et copier le jeton affiché une seule fois.
2. Fournir les secrets au processus PHP par variables d'environnement, puis
   définir dans `config/mes_options.php` :

```php
define('_HDP_BRIDGE_URL', getenv('HDP_BRIDGE_URL') ?: '');
define('_HDP_BRIDGE_TOKEN', getenv('HDP_BRIDGE_TOKEN') ?: '');
```

3. Installer et activer le plugin. Le cron SPIP interroge HDP toutes les cinq
   minutes via HTTPS. Ne placez jamais le jeton dans l'interface, le dépôt, une
   URL ou les journaux.
4. Créer un compte SPIP nominatif par visiteur. Les pages `spip.php?page=hdp`
   et `spip.php?page=hdp_publication` n'affichent rien aux visiteurs anonymes et
   désactivent le cache partagé.

Le plugin publie automatiquement dans l'espace protégé uniquement après la
décision manuelle HDP. Cette décision, l'import, les mises à jour et les retraits
sont tracés par la passerelle `hdp-spip/1.0`.
