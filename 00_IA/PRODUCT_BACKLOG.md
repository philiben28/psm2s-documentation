# PSM2S - PRODUCT BACKLOG

## Priorité 1 (En cours)

### Calendrier Réglementaire Intelligent

Objectif :

Créer le cœur du pilotage de PSM2S.

Fonctions attendues :

- Vue Mois
- Vue Semaine
- Vue Jour
- Calcul automatique des échéances
- Couleurs de conformité
- Ouverture directe de la fiche contrôle
- Mise à jour automatique après validation

Priorité : CRITIQUE

---

## Priorité 2

### Tableau de bord Directeur

Objectif :

Présenter la situation de l'établissement en moins de 30 secondes.

Fonctions :

- Score de conformité
- Contrôles en retard
- Échéances proches
- Dernières actions

---

## Priorité 3

### Widget "Mes prochaines actions"

Afficher les 5 prochaines actions importantes.

Chaque ligne doit ouvrir directement la fiche concernée.

---

## Priorité 4

Alertes automatiques

---

## Priorité 5

Assistant IA spécialisé

---

## Phase 4 — Candidats identifiés au-delà du backlog écrit

### Référentiel des partenaires (Prestataire)

Constat d'origine : le référentiel `Prestataire` (P4-L3, 05/07/2026)
n'avait d'écran nulle part — auto-créé uniquement à partir du nom saisi
dans le formulaire de contrat (`get_or_create_normalise`), qui ne
renseigne que le nom. Découvert le 05/07/2026 pendant la vérification
fonctionnelle du correctif Contrats sur formation. Pas une anomalie :
évolution fonctionnelle logique après P4-L3, pas une correction de
comportement incorrect. Découpage complet et décision de périmètre dans
`DECISIONS.md` (§ P4-L4).

- **P4-L4 — FAIT (05/07/2026)** : liste des partenaires et fiche par
  prestataire, en lecture seule (coordonnées, établissements où il
  intervient, type de contrôle concerné, dates premier contrat/dernière
  intervention contractuelle), lien direct depuis la fiche Contrat.
  Aucune migration.
- **P4-L5 (à ouvrir après retour d'usage de L4)** : écran de
  création/modification d'un Prestataire (nom, contact, téléphone, email,
  adresse, site web) ; remplacement du champ texte libre du formulaire
  Contrat par une recherche parmi les prestataires existants.
- **P4-L6 (candidat, non garanti)** : suggestion proactive de
  prestataires pertinents à la création d'un contrat ou d'un
  établissement — à confirmer seulement si le besoin se vérifie après
  L4/L5.