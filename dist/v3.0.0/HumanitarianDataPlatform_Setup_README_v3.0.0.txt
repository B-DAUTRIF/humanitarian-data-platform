Humanitarian Data Platform — installateur Windows natif 3.0.0
==================================================================

Fichier principal
-----------------
HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe

Version 3.0.0 — exécutable final
-------------------------------------------
- versions immuables et exécution Python/R bornée dans des runners non
  privilégiés et sans réseau ; rapports JSON avec empreintes SHA-256 ;
- abonnements aux quatre flux RSS officiels ReliefWeb et lecture planifiée ;
- chronologie Gantt des acquisitions, planifications et exécutions ;
- import GeoJSON PostGIS, Leaflet 1.9.4 embarqué et exports QGIS/R ;
- fond OpenStreetMap désactivé par défaut et activable explicitement ;
- passerelle REST GitHub locale avec lectures classiques et écritures
  désactivées par défaut ;
- registre versionné des paramètres globaux et par projet pour les 7 APIs ;
- prévisualisation des URL et commandes sans exécuter la requête ;
- paramètres complets archivés avec acquisitions et planifications ;
- bibliothèque filtrable par source, format, sujet, organisme et localisation ;
- migrations idempotentes et conservation des variables `.env` inconnues ;
- détection explicite d'une installation existante et sauvegarde préalable de
  `.env` sous `.env.backup-before-v3.0.0` ;
- conservation des variables `.env` inconnues, de `data` et du volume PostgreSQL ;
- compatibilité de structure contrôlée depuis 2.5.0 ; les migrations cumulatives
  1.5–2.4 sont conservées mais leur recette exige des sauvegardes représentatives ;
- EXE réellement compilé pour Windows x64 et contrôlé comme PE32+ GUI avec
  ASLR/NX ; l'essai d'installation sur Windows reste à effectuer.

Socle conservé depuis 2.5.0
---------------------------
- catalogue intégré de 18 sources épidémiologiques et sanitaires mondiales ;
- 7 sources interrogeables et planifiables : HDX, ReliefWeb, OMS/GHO, Banque
  mondiale/WDI, UNICEF/SDMX, ONU/ODD et DHS ;
- 11 portails de référence affichés avec leurs domaines et contraintes d'accès ;
- archivage de chaque réponse distante brute avec empreinte SHA-256 ;
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
3. Lancez HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe.
4. Conservez le dossier proposé pour mettre à niveau une installation existante.

Le volume PostgreSQL, le fichier .env, les réponses brutes et les ressources
locales sont conservés. Avant réécriture, `.env` est sauvegardé sous
`.env.backup-before-v3.0.0` et toute variable non gérée par l'installateur est
recopiée. Un ancien profil pays est préservé avec COD-AB. Une
ancienne portée monde/région est suspendue jusqu'au choix explicite d'un pays
ou d'une zone dans la liste ONU M49 × HDX.

Compatibilité
-------------
- 2.5.0 : chemin de mise à niveau ciblé et contrôlé dans les sources/tests ;
- 2.4.x, 2.3.x, 2.0 et 1.5 : migrations historiques cumulatives conservées ;
- retour vers une version antérieure : non pris en charge sans restauration
  d'une sauvegarde cohérente du volume PostgreSQL, de `.env` et de `data`.

Ne supprimez jamais le volume Docker et n'utilisez pas `docker compose down -v`
lorsque les données doivent être conservées.

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
une confirmation explicite dans les paramètres du projet. Préférez un jeton
finement granulé limité au compte/à l'organisation et à la permission de dépôt
Administration: write requise pour créer le dépôt.

Géodonnées ONU M49 et familles COD
----------------------------------
HDP vérifie les identifiants cod-ab-<iso3> et cod-ps-<iso3> ainsi que l'unique
groupe ISO3 ONU M49. COD-AB n'accepte que cod-enhanced ou cod-standard. COD-PS
utilise les ressources tabulaires officielles. La liste n'affiche que les pays
ou zones présents dans toutes les familles choisies.

ReliefWeb
---------
ReliefWeb exige un appname pré-approuvé. Sans cette valeur, les fonctions HDX
et les cinq nouveaux connecteurs sanitaires publics restent utilisables. Les
indicateurs DHS agrégés sont publics ; les microdonnées DHS/MICS nécessitent une
procédure distincte d'inscription et d'approbation.

Scripts et planifications
-------------------------
Python et R peuvent être exécutés hors ligne avec délai et sortie bornés ; SQL,
shell et « autre » restent stockés uniquement. Chaque modification crée une
version immuable. N'exécutez que du code local de confiance. Une planification
peut relancer une acquisition et télécharger ses ressources.

Journal et diagnostic
---------------------
Le fichier CHANGELOG_HDP.log est installé avec l'application. En cas d'échec,
lancez HDP_Diagnostic_v3.0.0.cmd puis relisez le fichier HDP_Debug_v3.0.0_*.log
créé sur le Bureau avant de le partager. Aucun secret .env n'est affiché.

Limites
-------
HDP 3.0.0 reste une application locale et ne doit pas être exposée directement
sur Internet. L'installateur n'est pas signé par un certificat d'éditeur. Le
format PE, le payload et les contrats de migration ont été contrôlés sous Linux ;
la première exécution doit être validée sur Windows 10/11 x64 avec Docker Desktop.
