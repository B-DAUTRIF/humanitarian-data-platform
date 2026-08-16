# Architecture et UML - HDP V5

La V5 conserve un monolithe modulaire : une interface, une API, un cœur PostgreSQL/PostGIS et deux runners. Le service GitHub secondaire a été retiré du déploiement car il dupliquait la logique et le secret. Les nouvelles fonctions résident dans `v5_features.py`; le fichier `main.py` conserve l’orchestration historique en vue d’une extraction progressive par domaines.

## Vue de composants

```mermaid
flowchart TB
    U["Interface locale V5"] --> A["API FastAPI authentifiée"]
    A --> C["Cœur acquisition et projets"]
    A --> I["Intelligence HDX"]
    A --> N["Notebooks et scripts"]
    C --> D[("PostgreSQL / PostGIS")]
    I --> D
    N --> D
    N --> Q["Spool borné"]
    Q --> P["Runner Python"]
    Q --> R["Runner R"]
    C --> X["Sources officielles HTTPS"]
    I --> H["HDX Data Grid / Signals"]
```

## Classes métier principales

```mermaid
classDiagram
    class Project
    class Acquisition
    class LocalResource {
      version_number
      expected_update_at
      reliability
      schema_metadata
    }
    class HdxMetadataRecord
    class SignalEvent
    class SignalRule
    class SignalAction
    class SyndromicSnapshot
    class Notebook
    class NotebookRevision
    class ScriptExecution
    Project "1" --> "*" Acquisition
    Acquisition "1" --> "*" LocalResource
    Project "1" --> "*" HdxMetadataRecord
    Project "1" --> "*" SignalRule
    Project "1" --> "*" SignalEvent
    SignalRule "1" --> "*" SignalAction
    SignalEvent "1" --> "*" SignalAction
    Project "1" --> "*" SyndromicSnapshot
    Project "1" --> "*" Notebook
    Notebook "1" --> "*" NotebookRevision
    NotebookRevision "1" --> "*" ScriptExecution
```

## Séquence signal vers données

```mermaid
sequenceDiagram
    participant E as Source du signal
    participant S as Moteur SIGNALS
    participant G as Recherche Data Grid
    participant D as Métadonnées HDX
    participant R as Actualisation
    E->>S: événement structuré et preuves
    S->>S: dédoublonner et appliquer les règles
    S->>G: périmètre, thèmes, zone et période
    G->>D: indexer jeux et fichiers
    S->>R: ressources correspondantes et échues
    R-->>S: acquisitions/versionnements tracés
```

## Frontières de sécurité

- le navigateur doit présenter le secret de session local et un marqueur CSRF pour toute mutation ;
- l’API refuse les hôtes non autorisés et reste liée à la boucle locale ;
- les téléchargements épinglent une adresse IP publique validée, y compris après redirection ;
- le workspace SQL utilise `hdp_reader`, sans privilège, et une liste positive AST ;
- les runners n’ont aucun réseau, changent d’UID par job, tuent le groupe de processus et purgent le spool ;
- la restauration valide l’empreinte externe et le contenu avant extraction.
