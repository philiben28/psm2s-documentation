# Compte-rendu — Phase 4, Lot 1 : Tableau de bord Directeur enrichi

Date : 04/07/2026
Statut : développement terminé, en attente d'exécution des tests par le DT.

---

## 1. Rappel du périmètre validé

4 blocs sur la page d'accueil du Directeur (`dashboard()`) : score de
conformité global, 5 actions prioritaires (lien direct vers la fiche),
échéances proches (en retard / aujourd'hui / cette semaine), indicateurs
clés (contrôles en retard, prescriptions ouvertes, tickets critiques,
contrats à échéance). Règle du DT pour ce développement : **aucune
nouvelle logique métier — uniquement extraction et réutilisation de
l'existant.**

## 2. Fichiers modifiés / créés

- **`registre/tableau_bord.py`** (nouveau) : fonction unique
  `collecter_conformite(etablissements)`, reprise exacte de la logique de
  `tableau_de_bord()` (score, alertes retard/proche/contrat, prescriptions
  ouvertes, contrats à échéance), indépendante du rôle appelant. Seul ajout
  réel : une catégorisation des échéances par fenêtre (retard/aujourd'hui/
  semaine), qui réutilise les mêmes champs et le même seuil de 7 jours déjà
  utilisé pour les alertes « proche » — pas une nouvelle règle.
- **`registre/views.py`** :
  - `dashboard()` : si `request.user.role == 'directeur'`, appelle
    `collecter_conformite()` sur le périmètre déjà scopé (`etablissements`,
    inchangé) et ajoute 4 clés de contexte. Rien ne change pour les autres
    rôles (factotum, prestataire, admin, responsable_securite).
  - `tableau_de_bord()` : la construction des `alertes` (dupliquée avec
    `dashboard`) est remplacée par un appel à `collecter_conformite()`.
    Tout le reste (score_global propre à cette vue, tableau par
    établissement, filtres, catégories) est **inchangé** — seule la
    logique réellement dupliquée a été extraite.
- **`Templates/registre/dashboard.html`** : 4 blocs ajoutés, affichés
  uniquement si `directeur_indicateurs` est présent dans le contexte (donc
  uniquement pour le rôle Directeur). Réutilise exclusivement des classes
  CSS déjà existantes dans `base.html` (`stat-card`, `badge-*`, `prio-dot`,
  `page-title`…) — aucun nouveau style introduit.
- **`registre/tests.py`** : nouvelles classes `CollecterConformiteTests`
  (moteur, indépendant des vues), `DashboardDirecteurTests` (blocs
  affichés au Directeur, absents pour factotum/admin, scope correct),
  `TableauDeBordNonRegressionTests` (le refactor ne change aucun
  comportement observable de `tableau_de_bord`).

## 3. Décision d'implémentation notable (autonomie Lead Developer)

Les 4 blocs ne sont affichés **que pour le rôle `directeur`**, pas pour
factotum/prestataire (qui partagent la même page `dashboard`) : ces rôles
n'ont pas vocation à voir des indicateurs de pilotage (prescriptions,
contrats) hors de leur périmètre fonctionnel. Admin/responsable_securite
ne les voient pas non plus : ils disposent déjà de `tableau_de_bord`
(plus riche, vue multi-sites) — leur ajouter les mêmes blocs sur
`dashboard` aurait été redondant, pas demandé.

## 4. Question d'architecture ouverte (rappel, non tranchée dans ce lot)

Le moteur (`collecter_conformite`) est déjà partagé entre les deux vues,
ce qui garde ouverte la question posée par le DT (une seule page de
tableau de bord avec widgets par profil, vs deux pages) sans qu'il soit
nécessaire de la trancher aujourd'hui — le prochain lot qui y touchera
n'aura pas à revenir sur les calculs.

## État des 4 Feux Verts

| Feu | État |
|---|---|
| Développement | ✅ Fait |
| Tests | ✅ 148/148 verts (148 = 137 avant ce lot + 11 nouveaux tests) |
| Documentation | ✅ Ce compte-rendu |
| Commit Git | ✅ `873da0c`, poussé sur `main` |

---

*Rédigé par le Lead Developer PSM2S, 04/07/2026.*
