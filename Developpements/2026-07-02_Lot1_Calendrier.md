# Lot 1 — Calendrier Réglementaire (vue Mois)

Date : 02/07/2026
Statut : développé, en attente de validation du Product Owner (Étape 6 du protocole).

## Objet

Première brique du Calendrier Réglementaire Intelligent (priorité 1 du backlog) :
vue mensuelle des échéances des contrôles réglementaires, avec couleurs de
conformité, bandeau des contrôles en retard, légende, et ouverture directe de
la fiche contrôle au clic. HTML/CSS rendu serveur, sans dépendance JavaScript.

## Fichiers modifiés

### 1. `registre/views.py` (ajout uniquement)

Un seul bloc ajouté, encadré par les bannières
`LOT 1 — CALENDRIER RÉGLEMENTAIRE (début)` / `(fin)`, inséré après
`_calculer_prochaine_echeance` :

- `SEUIL_ORANGE_JOURS = 30` et `SEUIL_ROUGE_JOURS = 7` : seuils de couleur
  **paramétrables en une ligne** (vert > 30 j ; orange entre 30 et 7 j ;
  rouge < 7 j ou en retard).
- `_couleur_conformite(controle, today)` : calcule la couleur d'un contrôle.
- `_construire_grille_mois(...)` : grille des semaines via le module standard
  `calendar` (lundi → dimanche).
- Vue `calendrier(request)` : `@login_required`, filtrage par rôle via
  `_get_etab_ids_autorises` (réutilisé), requêtes bornées au mois affiché
  avec `select_related`. Statuts `pas_obligation` / `non_concerne` exclus.

### 2. `registre/urls.py` (une route ajoutée)

`path('calendrier/', views.calendrier, name='calendrier')`

### 3. `Templates/base.html` (un lien ajouté)

Lien « Calendrier » (icône `ti-calendar`) dans la section « Principal » de la
sidebar, avec le bloc `nav_calendrier`. Masqué aux prestataires, comme le lien
« Contrôles ».

## Fichier créé

### `Templates/registre/calendrier.html`

Étend `base.html`. Contient : bandeau rouge des contrôles en retard (tous mois
confondus, avec J+n), navigation ◀ Aujourd'hui ▶, légende 🟢🟠🔴, grille
mensuelle en tableau CSS. Chaque événement et chaque retard est un lien vers
`registre:modifier_controle` (fiche du contrôle). Styles conformes aux
variables CSS existantes (`--ok`, `--warn`, `--danger`…).

## Points d'attention

- Aucun modèle modifié, aucune migration, aucune dépendance externe.
- La fiche contrôle (`modifier_controle`) est réservée aux gestionnaires
  (admin / responsable / directeur) : un factotum cliquant sur un événement
  est redirigé vers le dashboard (comportement existant, inchangé).
- Sauvegarde avant modification : `PSM2S\Sauvegardes\2026-07-02_avant_Lot1_calendrier\`
  (copies de `urls.py` et `base.html` ; le bloc ajouté à `views.py` est
  réversible par suppression des bannières LOT 1).
- Aucun dépôt Git détecté dans le projet : un commit/push est recommandé
  avant mise en production.
- Vérification à effectuer sur l'environnement d'exécution :
  `python manage.py check` puis test visuel de `/calendrier/`.
