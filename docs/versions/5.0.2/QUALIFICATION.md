# Qualification de la livraison HDP 5.0.2

## Preuves GitHub

- commit source : `cfb42bbb9813f108a5087ad443c2a2d3fa561a06` ;
- workflow Windows : [`31947534163`](https://github.com/B-DAUTRIF/humanitarian-data-platform/actions/runs/31947534163), conclusion `success` ;
- workflow de validation : [`31947534199`](https://github.com/B-DAUTRIF/humanitarian-data-platform/actions/runs/31947534199), conclusion `success` ;
- artefact Actions : `HumanitarianDataPlatform-V5-complet`, identifiant `9263718612`.

## Contrôles rejoués lors de l’organisation

- archive Actions ZIP : test d’intégrité réussi ;
- archive complète interne : 232 entrées, test ZIP réussi, aucun chemin absolu ou `..` détecté ;
- installateur : PE32+ GUI x86-64 ;
- empreinte EXE : `0077049d4ec410a0594fa2743b0d6149c7b2c3ae4b08859bce1c219b9fe2814a` ;
- empreinte archive complète : `89e27edd1f5bdbf75bad70a66495843a8d777e3c73957cec534b56119d4345dc` ;
- empreinte archive Actions : `2917a21dc96e1da7add11b5b58987fed6dc7a19c39ae59a97da010d99e58637f`.

## Limites

La réussite des workflows ne remplace pas la recette manuelle Windows 10/11 sur le poste utilisateur. L’EXE reste non signé ; les tests de charge, d’intrusion indépendant et la revue métier restent ouverts.
