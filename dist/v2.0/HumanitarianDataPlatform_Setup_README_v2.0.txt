Humanitarian Data Platform — installateur Windows natif 2.0.0
================================================================

Fichier principal
-----------------
HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe

Nouveautés 2.0
--------------
- projets séparant ressources, préférences, scripts et planifications ;
- téléchargement automatique optionnel des ressources HDX/CKAN et des fichiers
  ReliefWeb présents dans les métadonnées ;
- planificateur persistant avec historique d'exécution ;
- inventaire local, téléchargement, vérification SHA-256 et suppression contrôlée ;
- scripts stockés et modifiables par projet, sans exécution automatique.

Installation ou mise à niveau
-----------------------------
1. Laissez Docker Desktop ouvert et opérationnel.
2. Vérifiez l'empreinte SHA-256 de l'installateur.
3. Lancez HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe.
4. Conservez le dossier proposé pour mettre à niveau une installation 1.5.

Le volume PostgreSQL, le fichier .env, les réponses brutes et les ressources
locales existantes sont conservés. Au premier démarrage, les acquisitions 1.5
sont rattachées au « Projet par défaut ». Aucune suppression de données n'est
effectuée par l'installateur.

Port et accès local
-------------------
L'application utilise 8080 s'il est disponible, sinon un port libre compris
entre 18080 et 18279. La valeur est enregistrée dans :

  %USERPROFILE%\HumanitarianDataPlatform\.env

Le service reste lié à 127.0.0.1 et n'est pas publié sur le réseau local.

Téléchargements automatiques
----------------------------
Ils sont désactivés par défaut. Chaque projet définit une limite de taille,
une limite de quantité et, facultativement, une liste de formats. Les URL non
HTTP(S), les identifiants intégrés et les adresses réseau privées sont refusés.
Les quotas et conditions d'utilisation des sources restent applicables.

ReliefWeb
---------
ReliefWeb exige un appname pré-approuvé. Vous pouvez le saisir dans
l'installateur. Sans cette valeur, HDX reste utilisable et l'application affiche
une instruction explicite pour activer ReliefWeb.

Scripts et planifications
-------------------------
Les scripts peuvent être créés et modifiés dans chaque projet, mais HDP 2.0 ne
les exécute pas. Une planification peut seulement relancer une acquisition et,
si demandé, télécharger les ressources correspondantes. L'intervalle minimal
est de 15 minutes.

Diagnostic
----------
En cas d'échec, lancez HDP_Diagnostic_v2.0.cmd puis joignez le fichier
HDP_Debug_v2.0_*.log créé sur le Bureau. Le diagnostic n'affiche pas le secret
PostgreSQL ni l'appname ReliefWeb.

Limites
-------
HDP 2.0 reste une application locale et ne doit pas être exposée directement
sur Internet. L'installateur n'est pas signé par un certificat d'éditeur.
