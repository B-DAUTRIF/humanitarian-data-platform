HUMANITARIAN DATA PLATFORM V6 — INSTALLATEUR WINDOWS
====================================================

Ce paquet installe l'interface HDP V6 d'exposition des paramètres API.

- HDP V6 est livré comme exécutable autonome Windows x64.
- Python n'est pas nécessaire au démarrage de cette interface.
- L'installateur propose toutefois Python 3.12 comme composant optionnel pour les scripts et traitements HDP.
- Une installation Python existante n'est ni supprimée ni remplacée.
- Si Python est absent et si winget est disponible, le composant optionnel utilise le paquet officiel Python.Python.3.12.
- Si winget est absent, HDP reste installable et l'utilisateur reçoit une information explicite.
- Installation par utilisateur dans %LOCALAPPDATA% : aucun droit administrateur HDP n'est requis.

Contrôles de qualification du build GitHub Actions :
1. compilation de l'application avec PyInstaller sur Windows Server 2025 ;
2. création de l'installateur avec NSIS ;
3. contrôle PE x64 / Windows GUI avec dumpbin ;
4. contrôle de la table d'import Windows ;
5. installation silencieuse dans un répertoire temporaire du runner ;
6. démarrage de l'application installée ;
7. appel HTTP local /api/health ;
8. vérification de 2057 paramètres et 10 sources ;
9. calcul SHA-256 ;
10. publication de l'artefact uniquement si tous ces contrôles réussissent.
