# PSM2S — Phase 3, Lot Calendrier 2 : vues Semaine et Jour
## Revue d'Architecture – Synthèse

Date : 03/07/2026 — Lead Developer PSM2S
Statut : en attente de validation du périmètre (Directeur Technique).

---

## Objectif

Ajouter deux granularités d'affichage (Semaine, Jour) à la vue calendrier
existante (Lot 1, vue Mois, validée). Même source de données
(`ControleEtablissement.prochaine_echeance`), aucun modèle touché.

## Périmètre — **seul point à valider**

Inclus : vues Semaine et Jour, même vue `calendrier()`, paramètre `vue=`
en query string (cohérent avec la navigation existante `?annee=&mois=`).

Exclu de ce lot (lots ultérieurs distincts) : filtres établissement/
catégorie, sources secondaires d'échéances (contrats, prescriptions,
tickets), seuils de couleur configurables en base.

## Fichiers impactés

`registre/views.py` (extension du bloc LOT 1 existant, deux fonctions de
construction de grille supplémentaires) ; deux templates créés pour les
grilles Semaine/Jour, avec la légende et le bandeau des retards
factorisés en partials communs avec la vue Mois. Aucune route nouvelle,
aucun changement dans `base.html`.

## Risques

Faibles : réutilisation stricte de `_couleur_conformite()` et
`_get_etab_ids_autorises()`, pas de migration, pas de dépendance externe.

## Décisions d'implémentation (autonomie Lead Developer, pour information)

Templates séparés (pas un fichier unique avec conditions) : plus lisible
à mesure que le calendrier gagnera des filtres et des sources. Semaine et
Jour traités comme un seul lot fonctionnel (même patron de code que le
Lot 1), avec deux commits distincts pour garder un historique lisible.

---

## Décision attendue du Directeur Technique

☐ Périmètre validé

☐ Périmètre à modifier

Après validation, le développement pourra débuter conformément à la
Méthodologie de Développement PSM2S.
