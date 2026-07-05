# PSM2S — Registre des anomalies

Document de suivi **permanent** du projet (validé par le Directeur Technique le 02/07/2026).

## Règle de gouvernance (DT, 02/07/2026)

> Une anomalie n'entre dans ce registre que lorsqu'elle est **identifiée ET décidée en revue technique**.

Autrement dit : ce registre n'est **pas** une liste d'idées, de souhaits ou de pistes.
Il ne contient que des anomalies **réelles, validées et planifiées** en revue.
Une piste simplement pressentie reste **hors registre** (dans le rapport d'audit ou un compte-rendu) jusqu'à ce qu'une revue la qualifie. Ce filtre est ce qui garde le registre utile dans le temps sans devenir une charge de maintenance.

Cycle de vie d'une entrée : `identifiée → décidée en revue → inscrite (Ouverte) → lot dédié → Résolue`.

---

## Ouvertes — identifiées et décidées en revue

### ACC-ZONE — Cohérence métier : `?zone=<pk>` dans `accessibilite_action_ajouter`
- **Nature** : validation de cohérence métier (**pas** un IDOR classique).
- **Fichier / vue** : `registre/views.py` — `accessibilite_action_ajouter`.
- **Description** : la vue récupère une zone optionnelle via `?zone=<pk>`
  (`get_object_or_404(EvaluationZone, pk=zone_pk)`) sans vérifier que cette zone
  appartient au registre de l'établissement courant.
- **Ce que ce n'est pas** : ni fuite de données (l'accès à l'établissement est
  contrôlé depuis C4-6), ni élévation de privilèges.
- **Risque réel** : intégrité — un paramètre forgé pourrait lier une action à une
  `EvaluationZone` d'un autre registre. Faible sévérité.
- **Décision en revue (02/07/2026)** : documentée, **non corrigée dans C4-6** ;
  à traiter dans un lot d'affinage « cohérence métier » distinct du contrôle IDOR.
- **Statut** : ouverte.

---

## Résolues

| Réf | Objet | Lot |
|---|---|---|
| C4-1 | IDOR Établissement | fait |
| C4-2 | IDOR Contrôles | fait |
| C4-3 | IDOR Documents / Tickets / Interventions | fait |
| C4-4 | IDOR Commissions / Contrats / Eau | fait |
| C4-5 | IDOR DUERP | fait |
| C4-6 | IDOR Registre d'Accessibilité | fait |
| C4-7 | IDOR Bâtiments — **clôture du chantier IDOR** | fait |
| BUG-TPL-01 | `modifier_batiment.html` étendait un template inexistant | fait |
| F9 | FORM-PERIMETRE — filtrage des formulaires (over-posting) | fait |
| M11 | Double `@classmethod` sur `peut_signer` (compat Python) | fait |
| E5 | Visibilité liste DUERP (`peut_tout_voir` / `duerp_liste`) | fait |
| IDOR-PDF | IDOR `registre_pdf` — oublié du sweep C4-1→C4-7, identifié et corrigé le 04/07/2026 (hors Phase 1) | fait |
| SETTINGS-FORMATION | `manage.py migrate` sans `DJANGO_SETTINGS_MODULE` explicite appliquait les migrations à `config.settings` au lieu de `config.settings_formation` (celui servi par Passenger) sur la plateforme formation — migrations 0019-0021 jamais appliquées à la vraie base jusqu'au 05/07/2026. Corrigé (migration 0019 fakée après vérification, 0020/0021 appliquées) ; `PROC-001`/`PROC-002` mis à jour pour l'empêcher à l'avenir | fait |
| DEBUG-FORMATION | `config/settings_formation.py` (fichier serveur, hors Git) redéfinissait `DEBUG = True`, écrasant le défaut sûr de `settings.py` — faille de sécurité active sur formation, jamais détectée faute d'avoir exécuté `check --deploy` sous le bon `DJANGO_SETTINGS_MODULE` avant le 05/07/2026. Corrigée sur le serveur (ligne supprimée, hérite désormais du défaut `False`) ; `security.W018` confirmé disparu après correction | fait |
| DB-NOM-FORMATION | Sauvegardes initiales du 05/07/2026 portaient sur `db.sqlite3`, alors que `settings_formation.py` configure `db_formation.sqlite3` comme base réelle — les premières sauvegardes de la journée ne protégeaient pas les données réellement utilisées. Base réelle sauvegardée a posteriori (`db_formation.sqlite3.bak-20260705`, taille vérifiée identique) ; `PROC-001` complété (Étape 0.2) pour vérifier le nom de la base avant toute sauvegarde future | fait |
| UI-PERM-CONTRATS | `detail_etablissement.html` masquait le bouton « Nouveau contrat » et les icônes Modifier/Supprimer aux Directeurs, alors que les vues correspondantes sont `@gestionnaire_requis` (admin, responsable_securite, directeur) — droit d'accès présent mais aucune affordance UI. Corrigé (3 occurrences ciblées, Contrats uniquement) ; test de non-régression ajouté | fait |

---

## Hors registre (par design)

Les autres constats du **rapport d'audit du 02/07/2026** (sécurité de production —
DEBUG, SECRET_KEY, médias servis sans auth, cookies ; mots de passe ; `is_staff` ;
uploads ; SQLite ; etc.) **ne figurent pas ici** tant qu'ils n'ont pas été
qualifiés en revue technique. Leur source de référence reste le rapport d'audit.
Ils seront inscrits au registre **au fur et à mesure** de leur passage en revue.

*Note de suivi (hors registre) : l'anomalie F2 — ligne dupliquée `user = request.user`
dans `duerp_supprimer_signature` — a été identifiée en C4-5 mais n'a pas encore été
décidée en revue ; elle n'entre donc pas au registre à ce stade, conformément à la
règle. À qualifier lors d'une prochaine revue si le DT le souhaite.*
