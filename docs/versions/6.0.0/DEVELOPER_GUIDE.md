# HDP V6.0.0 — Guide développeur

Le point d'entrée de production est `source/payload/api/app/main_v6.py`. Il réutilise le cœur historique `main.py`, puis monte les extensions V6, notamment la synchronisation GitHub et l'inventaire API.

Toute nouvelle source doit déclarer ses opérations et paramètres de façon à alimenter le catalogue canonique. Le critère de couverture n'est pas seulement qu'un paramètre soit accepté par le backend : il doit aussi être visible dans l'onglet **Inventaire API**, avec son type, son emplacement, sa description, son caractère obligatoire, sa classe d'accès et le contrôle UI recommandé.

Le build Windows doit compiler directement les sources V6. Il est interdit de faire dépendre une livraison qualifiée d'un remplacement temporaire de chaîne V5→V6 dans le runner CI.

Les tests de qualification doivent couvrir : cohérence de version, chargement du catalogue, comptages canoniques, montage du routeur, démarrage `main_v6`, compilation MSVC x64, structure PE et présence des composants embarqués.
