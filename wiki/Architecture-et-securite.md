# Architecture et sécurité

HDP conserve le monolithe modulaire V5 et ses runners isolés. La session
locale, l'analyse SQL AST, le rôle SQL dédié, l'épinglage IP des
téléchargements et la restauration prévalidée constituent les principales
frontières.

La V6 ajoute des règles immuables, des demandes d'action idempotentes, des
travaux de données par source et un catalogue de contrats. Les travailleurs
utilisent des baux bornés et des transactions PostgreSQL ; aucun exécuteur
externe n'est rendu automatique par défaut. Les sauvegardes sont restaurées
uniquement dans une base temporaire neuve après contrôle du manifeste et des
empreintes.

Le plugin SPIP ne reçoit ni runner ni secret HDP. Les messages importés sont
limités aux données publiques et leurs pièces jointes restent confinées. Les
recettes Internet, antimalware, Windows/Docker et SPIP/HTTPS demeurent des
portes de qualification séparées.
