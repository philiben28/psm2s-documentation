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
