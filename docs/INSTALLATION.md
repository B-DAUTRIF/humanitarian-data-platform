# Installation et première utilisation

## 1. Prérequis

| Élément | Exigence ou recommandation |
|---|---|
| Système | Windows 10/11 x64 pris en charge par Docker Desktop ; Windows 11 conseillé |
| Virtualisation | Virtualisation matérielle activée dans le BIOS/UEFI |
| WSL | WSL 2 compatible avec la version courante de Docker Desktop |
| Mémoire | 8 Go de RAM au minimum ; davantage pour R et les données volumineuses |
| Disque | 10 Go libres recommandés |
| Réseau | Connexion Internet pour winget, les images Docker et les API distantes |
| Navigateur | Navigateur Windows moderne |
| winget | Windows Package Manager, fourni par App Installer sur les versions modernes de Windows |

Docker Desktop est requis à l'exécution. Git et Visual Studio Code ne sont proposés que pour le développement. L'installateur ne coche automatiquement aucune installation tierce : l'utilisateur choisit et confirme les composants.

## 2. Télécharger et contrôler le paquet

Le paquet conseillé est [`HumanitarianDataPlatform_Windows_v1.5.zip`](../dist/HumanitarianDataPlatform_Windows_v1.5.zip). Il contient :

- l'installateur graphique Windows ;
- son empreinte SHA-256 ;
- une notice courte ;
- le script de diagnostic.

Après décompression, vérifiez l'exécutable dans PowerShell :

```powershell
Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe -Algorithm SHA256
```

Empreinte attendue :

```text
1e77042dbbd7a7d400c690076bc61e3c7191c5e928cdb016a39292af2a362470
```

L'exécutable n'est pas signé par un certificat d'éditeur. Windows SmartScreen peut donc afficher un avertissement. Ne poursuivez que si le nom du fichier, sa provenance et son empreinte correspondent.

## 3. Utiliser l'installateur

1. Ouvrez Docker Desktop s'il est déjà installé.
2. Lancez `HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe`.
3. Conservez de préférence le dossier `%USERPROFILE%\HumanitarianDataPlatform`.
4. Laissez l'appname ReliefWeb vide pour utiliser uniquement HDX, ou saisissez l'identifiant pré-approuvé.
5. Sélectionnez Docker Desktop seulement s'il est absent et si son installation est autorisée.
6. Sélectionnez Git et Visual Studio Code uniquement pour un usage de développement.
7. Activez R/plumber seulement si le module analytique est souhaité et si l'espace disque est suffisant.
8. Utilisez **Analyser à nouveau** si l'état d'une dépendance vient de changer.
9. Cliquez sur **Installer et ouvrir**, vérifiez le résumé, puis confirmez.

L'installateur exécute ensuite les opérations suivantes :

1. installation par winget des logiciels tiers explicitement sélectionnés ;
2. écriture du payload FastAPI, PostgreSQL/PostGIS et R/plumber ;
3. choix d'un port local disponible ;
4. création ou mise à jour de `.env` en conservant le secret PostgreSQL existant ;
5. vérification du moteur Docker ;
6. téléchargement de PostGIS et construction de l'API ;
7. construction facultative du service R ;
8. démarrage Docker Compose et attente des contrôles de santé ;
9. validation de `/api/health` puis ouverture du navigateur.

Le premier démarrage de Docker Desktop peut demander d'accepter ses conditions ou de mettre WSL à jour. Cette étape doit être terminée directement dans Docker Desktop.

## 4. Port local et adresses

Le port interne de FastAPI reste `8080`. Côté Windows, l'installateur :

1. réutilise `HDP_PORT` si l'application y répond ou si le port est disponible ;
2. essaie `8080` ;
3. sinon choisit le premier port libre entre `18080` et `18279` ;
4. écrit le résultat dans `%USERPROFILE%\HumanitarianDataPlatform\.env`.

Pour `HDP_PORT=18080`, les adresses sont :

| Fonction | Adresse |
|---|---|
| Interface | `http://localhost:18080` |
| Santé | `http://localhost:18080/api/health` |
| API interactive | `http://localhost:18080/docs` |
| Historique | `http://localhost:18080/api/acquisitions` |

Le service est lié à `127.0.0.1` et n'est pas publié sur le réseau local.

## 5. Première recherche

### HDX / CKAN

1. Choisissez **HDX / CKAN**.
2. Saisissez au moins deux caractères, par exemple `choléra Mozambique`.
3. Choisissez de 1 à 100 résultats.
4. Cliquez sur **Rechercher et archiver**.

La v1.5 recherche les métadonnées des jeux de données. Elle ne télécharge pas encore leurs fichiers de ressources.

### ReliefWeb

ReliefWeb nécessite un `appname` pré-approuvé. Sans cette valeur, HDP renvoie une erreur 503 explicite et HDX reste disponible. Après modification manuelle de `RELIEFWEB_APPNAME` dans `.env`, exécutez `stop-hdp.cmd`, puis `start-hdp.cmd`.

## 6. Démarrer et arrêter

| Script installé | Action |
|---|---|
| `start-hdp.cmd` | Démarre PostgreSQL et l'API, puis ouvre l'interface |
| `start-hdp-with-r.cmd` | Démarre aussi le profil analytique R |
| `stop-hdp.cmd` | Arrête les services en conservant les données |

La réinstallation réécrit le payload applicatif, mais conserve le mot de passe PostgreSQL lisible dans `.env`, l'appname existant en l'absence d'une nouvelle valeur, les images Docker et le volume PostgreSQL.
