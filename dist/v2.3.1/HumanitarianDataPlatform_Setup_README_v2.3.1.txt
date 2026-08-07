Humanitarian Data Platform — installateur Windows natif 2.3.1
==================================================================

Fichier principal
-----------------
HumanitarianDataPlatform_Setup_Native_GUI_v2.3.1.exe

Sous-version 2.3.1
------------------
- périmètre géographique choisi dans les 278 éléments de la nomenclature ONU M49 ;
- suppression de la saisie libre d'un identifiant HDX dans le module géographique ;
- sélection exclusive des COD-AB officiels OCHA/HDX ;
- choix entre COD amélioré uniquement ou COD amélioré avec standard en repli ;
- traçabilité du code M49, ISO3, niveau COD, éditeur, licence et date HDX ;
- reprise progressive des ressources reportées par la limite d'un passage ;
- conservation de la création GitHub, des projets, ressources, préférences,
  scripts et planifications introduits en 2.3.0.

Installation ou mise à niveau
-----------------------------
1. Laissez Docker Desktop ouvert et opérationnel.
2. Vérifiez l'empreinte SHA-256 de l'installateur.
3. Lancez HumanitarianDataPlatform_Setup_Native_GUI_v2.3.1.exe.
4. Conservez le dossier proposé pour mettre à niveau une installation existante.

Le volume PostgreSQL, le fichier .env, les réponses brutes et les ressources
locales sont conservés. Un ancien profil « monde » devient ONU M49 001. Une
ancienne portée plus étroite est suspendue jusqu'à ce que vous choisissiez un
territoire M49 : HDP ne déduit jamais arbitrairement un pays ou une région.

Port et accès local
-------------------
L'application utilise 8080 s'il est disponible, sinon un port libre compris
entre 18080 et 18279. La valeur est enregistrée dans :

  %USERPROFILE%\HumanitarianDataPlatform\.env

Le service reste lié à 127.0.0.1 et n'est pas publié sur le réseau local.

Téléchargements automatiques
----------------------------
Ils sont désactivés par défaut. Chaque projet définit une limite de taille et
de quantité. Une ressource déjà présente ne consomme plus le quota du passage ;
les ressources excédentaires sont reportées. Les URL privées sont refusées.

GitHub
------
Le jeton GitHub facultatif est masqué dans l'installateur et conservé dans .env.
Il n'est ni journalisé, ni renvoyé par l'API. La création d'un dépôt nécessite
une confirmation explicite dans les paramètres du projet.

Géodonnées ONU M49 et COD-AB
----------------------------
Le référentiel de périmètre provient de la Division de statistique des Nations
Unies. HDP interroge la série HDX « COD - Subnational Administrative Boundaries »
et n'accepte que cod-enhanced ou cod-standard. Les groupements M49 sont destinés
à l'usage statistique et n'impliquent aucune position politique.

ReliefWeb
---------
ReliefWeb exige un appname pré-approuvé. Sans cette valeur, les fonctions HDX
restent utilisables.

Scripts et planifications
-------------------------
Les scripts sont stockés et modifiables mais ne sont pas exécutés. Une
planification peut relancer une acquisition et télécharger ses ressources.

Journal et diagnostic
---------------------
Le fichier CHANGELOG_HDP.log est installé avec l'application. En cas d'échec,
lancez HDP_Diagnostic_v2.3.1.cmd puis relisez le fichier HDP_Debug_v2.3.1_*.log
créé sur le Bureau avant de le partager. Aucun secret .env n'est affiché.

Limites
-------
HDP 2.3.1 reste une application locale et ne doit pas être exposée directement
sur Internet. L'installateur n'est pas signé par un certificat d'éditeur.
