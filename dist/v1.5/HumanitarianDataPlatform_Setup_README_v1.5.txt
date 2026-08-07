Humanitarian Data Platform — installateur Windows natif 1.5.0
================================================================

Fichier principal
-----------------
HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe

Diagnostic du journal transmis
------------------------------
Le moteur Docker fonctionne désormais. L'image PostgreSQL/PostGIS a été
téléchargée, l'API Python a été construite et la base a été initialisée puis
déclarée saine.

Le seul blocage observé se produit lors de la publication du port Windows 8080 :

  listen tcp4 127.0.0.1:8080: bind: An attempt was made to access a socket
  in a way forbidden by its access permissions.

Sous Windows, ce message signifie généralement que le port est déjà utilisé ou
qu'il appartient à une plage de ports réservée/exclue. Il ne signale pas une
erreur de FastAPI, PostgreSQL, PostGIS ou Docker Compose.

Correction apportée en version 1.5
----------------------------------
Avant de lancer Docker Compose, l'installateur teste le port local configuré.
Il utilise 8080 s'il est libre ; sinon, il choisit automatiquement un port libre
entre 18080 et 18279. Ce choix est enregistré dans :

  %USERPROFILE%\HumanitarianDataPlatform\.env

La publication Docker, la sonde de santé, l'ouverture du navigateur et les
scripts start-hdp.cmd/start-hdp-with-r.cmd utilisent tous cette même valeur.
Le service reste lié à 127.0.0.1 et n'est donc pas publié sur le réseau local.

Relance recommandée
-------------------
1. Laissez Docker Desktop ouvert et opérationnel.
2. Lancez HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe.
3. Choisissez l'installation. Le volume PostgreSQL et les images déjà
   téléchargées sont conservés ; l'API sera seulement recréée avec le port libre.
4. L'installateur ouvrira automatiquement la bonne adresse locale.

Espace disque à corriger
------------------------
Le diagnostic transmis ne signalait qu'environ 1,59 Go libres sur C:. Ce n'est
pas la cause du refus du port 8080, mais c'est insuffisant pour travailler
sereinement avec les images, les volumes et le cache Docker. Libérez au moins
10 Go avant d'ajouter le module R ou de charger des jeux de données importants.

Si un autre disque est disponible, Docker Desktop permet aussi de déplacer son
image disque depuis Settings > Resources > Advanced > Disk image location.
N'utilisez pas Clean/Purge data ni Reset to factory defaults si vous souhaitez
conserver les images et le volume PostgreSQL existants.

Module R
--------
Le module R/plumber reste facultatif. Le cœur Python/PostGIS est utilisable sans
lui. Vous pourrez relancer l'installateur plus tard et sélectionner R lorsque
l'espace disque sera suffisant.

Diagnostic v1.5
---------------
En cas de nouvel échec, lancez HDP_Diagnostic_v1.5.cmd puis joignez le fichier
HDP_Debug_v1.5_*.log créé sur le Bureau. Cette version recense également les
ports TCP occupés/réservés, les contextes Docker, les distributions WSL et
l'espace libre, tout en bornant chaque commande à 15 secondes.
