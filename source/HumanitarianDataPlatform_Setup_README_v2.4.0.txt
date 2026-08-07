Humanitarian Data Platform — installateur Windows natif 2.4.0
==================================================================

Fichier principal
-----------------
HumanitarianDataPlatform_Setup_Native_GUI_v2.4.0.exe

Sous-version 2.4.0
------------------
- liste des téléchargements officiels COD-AB et COD-PS sélectionnables ;
- COD-CS visible mais désactivé tant que le registre vérifié est vide ;
- COD-HP affiché comme famille retirée par OCHA ;
- pays ou zone choisi dans l'intersection ONU M49 et groupes HDX canoniques ;
- 163 options COD-AB, 146 COD-PS et 143 communes vérifiées le 7 août 2026 ;
- format géospatial choisi pour COD-AB et ressources CSV/XLSX pour COD-PS ;
- synchronisation atomique : aucune famille partielle téléchargée en cas d'absence ;
- choix entre COD amélioré uniquement ou COD amélioré avec standard en repli ;
- traçabilité de la famille, du code M49, ISO3, niveau, éditeur, licence et date ;
- reprise progressive des ressources reportées par la limite d'un passage ;
- conservation de la création GitHub, des projets, ressources, préférences,
  scripts et planifications introduits en 2.3.0.

Installation ou mise à niveau
-----------------------------
1. Laissez Docker Desktop ouvert et opérationnel.
2. Vérifiez l'empreinte SHA-256 de l'installateur.
3. Lancez HumanitarianDataPlatform_Setup_Native_GUI_v2.4.0.exe.
4. Conservez le dossier proposé pour mettre à niveau une installation existante.

Le volume PostgreSQL, le fichier .env, les réponses brutes et les ressources
locales sont conservés. Un ancien profil pays est préservé avec COD-AB. Une
ancienne portée monde/région est suspendue jusqu'au choix explicite d'un pays
ou d'une zone dans la liste ONU M49 × HDX.

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

Géodonnées ONU M49 et familles COD
----------------------------------
HDP vérifie les identifiants cod-ab-<iso3> et cod-ps-<iso3> ainsi que l'unique
groupe ISO3 ONU M49. COD-AB n'accepte que cod-enhanced ou cod-standard. COD-PS
utilise les ressources tabulaires officielles. La liste n'affiche que les pays
ou zones présents dans toutes les familles choisies.

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
lancez HDP_Diagnostic_v2.4.0.cmd puis relisez le fichier HDP_Debug_v2.4.0_*.log
créé sur le Bureau avant de le partager. Aucun secret .env n'est affiché.

Limites
-------
HDP 2.4.0 reste une application locale et ne doit pas être exposée directement
sur Internet. L'installateur n'est pas signé par un certificat d'éditeur.
