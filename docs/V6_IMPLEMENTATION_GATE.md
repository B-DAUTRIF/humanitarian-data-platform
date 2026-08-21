# Jalon obligatoire après chaque implémentation HDP V6

Ce jalon doit être répété après chaque nouvelle implémentation V6, qu'elle soit
fonctionnelle, technique, documentaire ou liée à une migration. Le succès d'un
lot antérieur ne dispense jamais le lot suivant de ses propres contrôles.

## Séquence obligatoire

1. relire l'état, la notice et les décisions applicables au lot ;
2. mettre à jour code, migrations, tests et documentation correspondante ;
3. exécuter `python tools/run_v6_quality_gate.py` ;
4. exécuter en plus les tests d'intégration propres aux composants modifiés ;
5. inscrire les résultats et les contrôles indisponibles dans `HDP_STATE.json` ;
6. mettre à jour la todo-list et le changelog sans fermer une tâche non prouvée ;
7. en cas de bug ou d'ambiguïté, arrêter le lot et reprendre le dialogue avec le
   propriétaire avant toute solution qui changerait le besoin ;
8. ne produire archive, installateur, commit, push ou fusion que sur instruction
   explicite et après le niveau de qualification correspondant.

Le contrôle automatisé couvre les tests Python, la syntaxe de tous les fichiers
Python, les migrations PostgreSQL, le JavaScript, le schéma OpenAPI et les
compilations C disponibles. Il signale séparément l'installateur Windows, Docker
et les appels
réels aux connecteurs : ces recettes ne sont jamais réputées exécutées par
déduction.

## Règle de blocage

Un contrôle automatisable en échec bloque l'implémentation suivante. Un contrôle
d'environnement indisponible ne rend pas le lot local invalide, mais interdit de
présenter ce lot comme qualifié pour cet environnement ou comme livraison finale.
