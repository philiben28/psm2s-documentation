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

- **P4-L4 — clos, dev et formation (05/07/2026)** : liste des partenaires
  et fiche par prestataire, en lecture seule (coordonnées, établissements
  où il intervient, type de contrôle concerné, dates premier
  contrat/dernière intervention contractuelle), lien direct depuis la
  fiche Contrat. Aucune migration. Périmètre par rôle vérifié en
  conditions réelles sur formation.
- **P4-L5 — Feu Vert accordé, en développement (05/07/2026)** : « Gestion
  complète d'un partenaire », un seul écran côté utilisateur. Combine la
  création/modification du référentiel partagé (`Prestataire` : nom,
  téléphone, email, adresse, site web) et un nouvel objet
  `CorrespondantLocal` — un « post-it » par couple (Prestataire,
  Établissement) : nom du correspondant, téléphone, email, notes libres,
  jamais partagé entre établissements. Point d'entrée « Nouveau
  partenaire » toujours scopé à un établissement. Modification du
  référentiel partagé réservée à admin/responsable_securite une fois créé ;
  chaque établissement gère librement son propre correspondant local.
  Détail complet du cadrage et de la décision d'architecture dans
  `DECISIONS.md`. Une migration (nouvelle table `CorrespondantLocal`),
  aucune donnée existante à transformer.
- **P4-L6 (ex-partie de l'ancien P4-L5)** : remplacement du champ texte
  libre du formulaire Contrat par une sélection parmi les prestataires
  existants, détection de doublons.
- **P4-L7 (candidat, non cadré, ex-P4-L6)** : Widget Directeur — les
  actions prioritaires. À définir en détail le moment venu.

### Contact Partenaire (futur, non numéroté — après P4-L5/L6)

Révélé le 05/07/2026 pendant le cadrage de P4-L5, à partir d'un exemple
réel (SOCOTEC : plusieurs agences, plusieurs techniciens, coordonnées
différentes par agence/technicien). `CorrespondantLocal` (P4-L5) répond
au besoin immédiat avec un seul correspondant par couple
(Prestataire, Établissement). Ce futur lot irait plus loin si le besoin
se confirme : plusieurs correspondants par établissement, fonctions,
téléphones directs par personne, notion d'agence — vient compléter
`CorrespondantLocal`, ne le remplace pas.

Nécessite : nouveau modèle Django, migration, formulaires, permissions,
vues, recherche — à ouvrir seulement quand le besoin sera mûr
(POLITIQUE-001), pas par anticipation. Non cadré, non numéroté tant que
P4-L5 n'a pas donné de retour d'usage réel.

### Signature électronique des bons d'intervention (futur, non numéroté)

Constat d'origine : en préparant le script de la vidéo de démonstration
(24/08/2026), tentative de montrer un factotum niveau 3 ("Signature des
interventions", cf. `Utilisateur.NIVEAU_FACTOTUM_CHOICES`) signer un
ticket/intervention. Vérification du code : le type de document
"Bon d'intervention" existe bien dans `DroitSignature.DOCUMENT_CHOICES`,
mais aucune vue ni aucun bouton "Signer" n'a jamais été développé pour
`TicketTravaux` / `Intervention` — seuls le DUERP et le Registre
d'Accessibilité disposent réellement du bouton de signature aujourd'hui
(cf. `views.py`, recherche `peut_signer`). Le niveau 3 factotum existe
donc dans le modèle sans fonctionnalité correspondante à activer.

Phil confirme le 24/08/2026 que ce sera nécessaire à terme (retour
pendant la préparation de la démo vidéo) : le libellé "Signature des
interventions" du niveau 3 doit correspondre à une action réelle,
cohérent avec la logique déjà en place pour le DUERP (`DroitSignature`,
`_copier_signature`, horodatage automatique).

Non cadré, non numéroté : pas de découpage de lot ni de Feu Vert à ce
stade — à ouvrir formellement (cadrage P4 ou phase suivante) quand ce
sera le tour de ce lot dans les priorités.