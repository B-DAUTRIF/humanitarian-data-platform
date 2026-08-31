# Avis professionnel de santé publique — HDP V7

## Périmètre de l'avis

Cet avis évalue HDP comme outil d'accès, de préparation et de traçabilité de données utiles en santé publique et en contexte humanitaire. Il ne constitue pas une validation clinique, une certification réglementaire ni une preuve d'efficacité d'un système de surveillance en population réelle.

Le cadre d'analyse reprend les attributs classiques d'évaluation des systèmes de surveillance : utilité, simplicité, flexibilité, qualité des données, acceptabilité, sensibilité, valeur prédictive positive, représentativité, promptitude et stabilité. Pour HDP, plusieurs de ces attributs ne peuvent pas encore être mesurés en population réelle.

## Avis synthétique

HDP est actuellement plus crédible comme **plateforme technique de découverte, interrogation, normalisation, provenance et reproductibilité multi-sources** que comme système opérationnel de surveillance épidémiologique. La distinction est importante. Le logiciel sait interroger plusieurs fournisseurs, expliciter leurs paramètres et produire des requêtes reproductibles ; cela ne démontre pas qu'il détecte correctement un signal sanitaire, qu'il est représentatif d'une population, ni qu'il améliore une décision de santé publique.

### Utilité

L'utilité potentielle est réelle pour un analyste qui doit retrouver et comparer des données provenant d'organismes différents, particulièrement lorsque la requête native, la source et les transformations sont conservées. En revanche, l'utilité opérationnelle n'est pas encore démontrée par une étude montrant que HDP raccourcit un délai d'analyse, améliore une investigation ou modifie favorablement une décision de santé publique.

### Simplicité et acceptabilité

L'exposition détaillée des paramètres fournisseur améliore la transparence mais augmente fortement la complexité cognitive. Les modes Simple/Avancé/Expert sont donc nécessaires, mais leur qualité ne peut pas être déduite des tests automatisés. Il manque une évaluation d'utilisabilité avec des profils réels : épidémiologiste, data manager, chargé de surveillance, clinicien de terrain et utilisateur R/Python. Sans cette étude, l'acceptabilité reste **À VÉRIFIER**.

### Flexibilité

L'architecture par descriptors/services et l'isolation des connecteurs sont favorables à la flexibilité. Le fait de préserver les paramètres natifs évite de réduire toutes les sources à un modèle artificiellement uniforme. Le coût de cette flexibilité est une maintenance importante : évolution des API, codelists, nomenclatures, authentifications et contrats SDMX/OData doivent être surveillés.

### Qualité des données

HDP améliore la traçabilité technique, mais la qualité d'une donnée ne découle pas de la réussite HTTP de son téléchargement. Il faut distinguer qualité du transport, complétude du jeu, validité des valeurs, cohérence temporelle, stabilité des définitions, révisions rétrospectives et biais de collecte. La plateforme devrait produire un profil de qualité par dataset : date de mise à jour, période couverte, valeurs manquantes, doublons, ruptures de série, changements de définition, granularité, provenance et éventuels avertissements du producteur.

### Représentativité, sensibilité et valeur prédictive positive

Ces trois attributs ne sont **pas qualifiés** par les tests actuels. Ils nécessitent un objectif de surveillance défini, une population cible, une définition de cas/signal et une référence permettant d'estimer les événements manqués et faux positifs. Une agrégation multi-source ne doit jamais être présentée comme représentative simplement parce qu'elle couvre plusieurs fournisseurs.

### Promptitude

La plateforme doit distinguer au minimum : date de l'événement, date de collecte, date de notification au fournisseur, date de publication/révision, date d'ingestion HDP et date de consultation. Sans ces horodatages, un utilisateur peut confondre une requête rapide avec une donnée récente. Des métriques de fraîcheur et de retard devraient devenir des objets de première classe.

### Stabilité

Les régressions et sentinelles live apportent une preuve technique utile contre les ruptures de connecteurs. Elles ne remplacent cependant pas une mesure longitudinale de disponibilité. Il faut suivre dans le temps taux de succès, changements de schéma, latence, indisponibilités, erreurs de mapping et dérive des vocabulaires.

## Risques prioritaires

1. **Fausse comparabilité.** Deux indicateurs portant des libellés proches peuvent différer par définition, dénominateur, période, population ou méthode de collecte.
2. **Faux sentiment d'exhaustivité.** Une interface unique peut donner l'impression que les données disponibles représentent l'ensemble de la situation sanitaire alors que la couverture dépend des fournisseurs et pays.
3. **Confusion disponibilité/fraîcheur.** Une API qui répond 200 peut fournir une série ancienne ou révisée tardivement.
4. **Risque de mapping.** Géographies, indicateurs et dimensions doivent rester accompagnés de la preuve de traduction ; les blocages en absence de mapping vérifié doivent être conservés.
5. **Dépendance aux API externes.** Une modification silencieuse de schéma ou de définition peut être plus dangereuse qu'une panne franche.
6. **Complexité utilisateur.** L'exposition exhaustive des paramètres est utile aux experts mais peut provoquer des requêtes incohérentes chez les utilisateurs moins familiers des modèles fournisseurs.
7. **Surveillance non démontrée.** Les capacités actuelles de collecte et de traitement ne suffisent pas à qualifier HDP comme dispositif de surveillance syndromique ou d'alerte.

## Priorités avant usage opérationnel de surveillance

P0 : dictionnaire sémantique versionné des indicateurs et dimensions ; profil qualité/fraîcheur systématique ; distinction stricte `no data` / erreur / requête partielle / mapping incertain ; audit des transformations et provenance exportable.

P1 : étude d'utilisabilité sur scénarios de santé publique réels ; benchmark de délais ; jeu de référence permettant de tester complétude, représentativité et détection ; règles de gestion des révisions de données.

P2 : tableaux de bord de stabilité des fournisseurs ; validation par domaine pour quelques cas d'usage ciblés (par exemple surveillance d'une maladie ou suivi d'un indicateur), plutôt qu'une prétention générale de validation épidémiologique.

## Conclusion

Pour un professionnel de santé publique, HDP V7 est à considérer aujourd'hui comme un **outil d'ingénierie et d'accès aux données en phase de qualification utilisateur**, pas comme un système de surveillance validé. Sa valeur dépendra moins du nombre de connecteurs que de sa capacité à rendre visibles les limites des données, les définitions, la fraîcheur, la couverture et chaque transformation. Le critère de réussite futur devrait être : « l'utilisateur peut-il déterminer rapidement si une donnée est adaptée à sa question de santé publique et reproduire exactement son acquisition et sa transformation ? »
