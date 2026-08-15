# Registre de décisions — Humanitarian Data Platform 3.0.0 finale

## D01 — Version figée

La version de production est 3.0.0, sans suffixe d'itération dans l'interface,
l'API, l'installateur ou les livrables finaux. Les sections d'itération sont
conservées uniquement comme historique dans les changelogs.

## D02 — Compatibilité

La mise à niveau garantie est ciblée depuis 2.5.0. Les versions antérieures ne
sont pas déclarées compatibles directement sans fixtures et recette dédiées.

## D03 — Exécution de scripts

Seuls Python et R sont exécutables. Le runner C appelle directement le moteur,
sans shell, sans réseau et avec des limites de ressources. Cette frontière ne
transforme pas HDP en sandbox multi-tenant : les scripts restent du code local
de confiance.

## D04 — GitHub à droits minimaux

Le jeton GitHub reste dans `.env`. Les opérations de lecture sont isolées dans
une passerelle locale. La création d'issues et le dispatch de workflows sont
désactivés par défaut et nécessitent un choix explicite ainsi que les seules
permissions fines utiles.

## D05 — Cartographie

Leaflet 1.9.4 est embarqué. Les tuiles OpenStreetMap sont opt-in, avec
attribution, sans préchargement ni téléchargement massif.

## D06 — Dépendances facultatives

R/plumber reste dans le profil Compose `analytics`. L'installation de Git et VS
Code peut être proposée, mais aucune option facultative n'est présélectionnée.

## D07 — Publication

La publication finale doit être un commit descendant du `main` observé,
préserver les livrables historiques et mettre à jour la branche sans force.
L'absence de licence HDP impose de conserver le dépôt privé.

## D08 — Limites de recette

La compilation PE, les tests locaux et les validations statiques sont séparés
de la recette Windows/Docker. Une opération non exécutable dans l'environnement
de construction est consignée comme limite et jamais déclarée réussie.
