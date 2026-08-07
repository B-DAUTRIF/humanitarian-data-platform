# Construction de l'installateur 1.5.0

Le code de l'installateur est en C/Win32. Le paquet est compilé depuis Linux avec Zig 0.12.0-dev.1286, qui fournit la chaîne de compilation croisée Windows x64.

Prérequis : Node.js 20 ou supérieur et Zig compatible.

```bash
bash build.sh /chemin/vers/zig /chemin/vers/un-cache-temporaire
```

Le script :

1. transforme les fichiers de `payload/` en tableau binaire C ;
2. compile le manifeste et les métadonnées Windows ;
3. compile le programme Win32 avec avertissements traités comme erreurs ;
4. produit `HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe`.

Le programme cible Windows x64, utilise le sous-système graphique et dépend uniquement de DLL système Windows. Docker Desktop et les composants choisis sont téléchargés sur la machine de destination via `winget`, après sélection et confirmation explicites.

La version 1.5 conserve les sondes Docker bornées et le module R optionnel de la version 1.4. Avant le démarrage Compose, elle vérifie le port local demandé, réutilise le port configuré si possible, puis sélectionne automatiquement un port libre entre 18080 et 18279 lorsque 8080 est occupé ou réservé par Windows. Le choix est écrit dans `.env` et utilisé par Compose, la vérification de santé et les raccourcis de démarrage. Elle avertit également avant les téléchargements lorsque le disque qui contient `%LOCALAPPDATA%` dispose de moins de 5 Gio libres.
