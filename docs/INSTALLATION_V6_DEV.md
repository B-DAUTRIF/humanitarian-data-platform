# Installation de développement HDP 6.0.0

La version 6.0.0-dev n'est pas une livraison installable qualifiée. Ce document
décrit la configuration introduite par la reprise V6 ; les recettes Windows,
Docker et serveur Internet doivent encore être exécutées avant publication.

## Authentification locale par passkey

L'installateur et `install-linux.sh` créent les valeurs suivantes :

```dotenv
HDP_AUTH_MODE=passkey
HDP_WEBAUTHN_RP_ID=localhost
HDP_WEBAUTHN_ORIGIN=http://localhost:8080
HDP_COOKIE_SECURE=false
HDP_ALLOWED_HOSTS=localhost,127.0.0.1,api
```

Au premier accès, ouvrir `http://localhost:8080/`, saisir une seule fois
`HDP_LOCAL_TOKEN` depuis `.env`, puis enregistrer une passkey. Le secret n'est
jamais placé dans l'URL. Les accès suivants utilisent la passkey et une session
opaque de douze heures dont seule l'empreinte SHA-256 est conservée.

## Serveur Internet

Le conteneur API reste lié à `127.0.0.1`. Un reverse proxy HTTPS doit terminer
TLS et transmettre vers ce port local. Pour `https://hdp.example.org` :

```dotenv
HDP_AUTH_MODE=passkey
HDP_WEBAUTHN_RP_ID=hdp.example.org
HDP_WEBAUTHN_ORIGIN=https://hdp.example.org
HDP_COOKIE_SECURE=true
HDP_ALLOWED_HOSTS=hdp.example.org,localhost,127.0.0.1,api
```

L'application refuse de démarrer si une origine Internet n'est pas HTTPS, si le
RP ID ne correspond pas à l'origine ou si les cookies sécurisés sont désactivés.
Le proxy doit préserver l'en-tête `Host` public. Ne publiez jamais directement
le port PostgreSQL, les runners ou le port API sans proxy.

## Plugin SPIP

Le plugin se trouve dans `source/spip-plugin/hdp`. Il cible SPIP 4.2 à 4.4. Une
connexion créée dans la rubrique **Publication SPIP** affiche une seule fois un
jeton limité. Sur le serveur PHP, fournir :

```php
define('_HDP_BRIDGE_URL', getenv('HDP_BRIDGE_URL') ?: '');
define('_HDP_BRIDGE_TOKEN', getenv('HDP_BRIDGE_TOKEN') ?: '');
```

`HDP_BRIDGE_URL` doit être l'origine HTTPS de HDP et non celle de SPIP. Le cron
SPIP récupère les contenus publics déjà approuvés manuellement. Un compte
nominatif SPIP est requis par visiteur ; les squelettes du plugin désactivent le
cache partagé des pages protégées.

## Limites de qualification actuelles

- compilation et installation Windows non exécutées sur cet hôte ;
- recette Docker Compose indisponible ;
- syntaxe et installation natives du plugin non testées faute de PHP/SPIP ;
- aucun appel réel aux dix API ni aux flux RSS exécuté dans le jalon local ;
- aucune restauration de sauvegarde exécutée ;
- réception réseau des mails non choisie : seul l'import manuel EML public est
  implémenté.
