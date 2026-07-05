# Phase 4, Lot 1 — Tableau de bord Directeur enrichi (proposition d'analyse)

Date : 04/07/2026
Statut : **analyse, aucun développement engagé** — en attente de validation DT
avant Architecture puis Développement, conformément à `IA_RULES` §Avant toute
modification.

## Point de départ : ce qui existe déjà réellement

Avant de proposer quoi que ce soit, vérification de l'état réel du code par
rapport à `PRODUCT_BACKLOG.md` :

- **Priorité 1 — Calendrier Réglementaire Intelligent** : **complète**, y
  compris le dernier point (« mise à jour automatique après validation ») —
  `nouvelle_realisation` et `modifier_controle` recalculent déjà
  automatiquement `prochaine_echeance` via `_calculer_prochaine_echeance`
  à chaque saisie. Rien à faire ici.
- **Priorité 2 — Tableau de bord Directeur** : **partiellement réalisée,
  mais pas pour le Directeur**. Il existe déjà une vue `tableau_de_bord`
  riche (score de conformité en %, alertes triées par urgence, prescriptions
  ouvertes, contrats expirants) — mais elle est explicitement réservée à
  `admin` et `responsable_securite` (`@acces_requis('admin', 'responsable_securite')`,
  `registre/views.py` ligne 1587), car conçue comme une vue **multi-sites**
  (« vue consolidée du patrimoine »). C'est cohérent : un Directeur n'a pas
  besoin d'une vue multi-sites, mais il n'a aujourd'hui **aucun équivalent
  sur son propre périmètre**.
- Ce que voit réellement un Directeur en se connectant : la vue `dashboard`
  (route racine `/`), qui liste ses établissements rattachés avec un statut
  global (danger/warn/ok), un compte de contrôles en retard/à faire et de
  tickets ouverts — **sans score de conformité en %, sans distinction
  retard/échéance proche, et sans liste d'actions prioritaires**.
- **Priorité 3 — Widget "Mes prochaines actions"** : **non réalisée pour le
  Directeur**. La logique la plus proche (liste `alertes`, triée par urgence,
  limitée à 6 éléments) existe déjà dans `tableau_de_bord`, mais n'est pas
  exposée dans `dashboard`.

## Constat

L'écart entre la Vision (« Le Directeur doit pouvoir ouvrir PSM2S chaque
matin et comprendre en moins de 30 secondes... ») et la réalité actuelle
n'est pas dans le Calendrier — il est dans le fait que **le Directeur,
l'utilisateur explicitement visé par la Vision, n'a pas accès à la vue qui
réalise cette promesse.**

## Proposition (recommandation unique)

Enrichir la vue `dashboard` (page d'accueil du Directeur, déjà scopée à son
périmètre via `_get_etab_ids_autorises`) avec deux ajouts, en réutilisant
la logique déjà écrite et éprouvée dans `tableau_de_bord` plutôt qu'en la
dupliquant :

1. **Score de conformité global** (%), calculé comme dans `tableau_de_bord`
   (`taux = nb_fait * 100 / nb_total`), affiché en tête de page.
2. **Widget "Mes prochaines actions"** : les 5 actions les plus urgentes
   (retards en premier, puis échéances proches ≤ 7 jours), chacune ouvrant
   directement la fiche établissement concernée — réutilisation de la
   logique `alertes` de `tableau_de_bord`, réduite à 5 éléments et scopée
   au périmètre de l'utilisateur (déjà le cas pour `dashboard`).

**Justification du choix** : ferme l'écart Vision/réalité le plus direct et
le plus visible dès la connexion — exactement le type d'évolution qui « rend
PSM2S plus indispensable » (Règle d'or). Réutilise du code déjà testé plutôt
que d'introduire une nouvelle logique. Périmètre volontairement limité à
`dashboard` : ne touche pas à `tableau_de_bord` (déjà stable, Priorité 2
admin/responsable), ne touche pas au Calendrier (déjà complet).

**Hors périmètre de ce lot** (à ne pas mélanger, IA_RULES §Développement) :
Priorité 4 (alertes automatiques par email/notification — mécanisme
différent, déclenché hors consultation) et Priorité 5 (assistant IA) restent
des lots futurs distincts.

## Impact et risques

- Aucun impact sur le modèle de données (calcul à la volée, comme
  `tableau_de_bord`).
- Aucun changement de périmètre fonctionnel pour les autres rôles.
- Léger risque de performance si le nombre d'établissements par Directeur
  devait croître fortement — non significatif aujourd'hui (un Directeur a
  aujourd'hui 1 à quelques établissements rattachés), à surveiller si le
  modèle multi-clients (L3.4) change cette hypothèse.

## Validation requise avant Architecture détaillée

☐ Périmètre validé / ☐ Périmètre à modifier

---

*Rédigé par le Lead Developer PSM2S, 04/07/2026.*
