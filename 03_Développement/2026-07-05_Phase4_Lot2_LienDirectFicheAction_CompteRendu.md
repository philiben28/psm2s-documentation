# Compte-rendu — Phase 4, Lot 2 : lien direct vers la fiche depuis « Mes actions prioritaires »

Date : 05/07/2026
Statut : clos, 156/156 tests verts.

---

## 1. Origine du lot

Méthode adoptée par le DT pour choisir les lots fonctionnels de la Phase 4
(au-delà du backlog écrit) : identifier le plus grand écart entre la
promesse de la Vision et l'expérience vécue par un Directeur lors d'une
démonstration de dix minutes. En rejouant ce parcours juste après P4-L1,
l'écart trouvé est en réalité une exigence du backlog non totalement
respectée : Priorité 3 exige que « chaque ligne [du widget des actions]
doit ouvrir directement la fiche concernée » — ce que « Mes 5 actions
prioritaires » ne faisait pas (lien vers `detail_etablissement`, pas vers
la fiche du contrôle/contrat).

## 2. Fichiers modifiés

- **`registre/tableau_bord.py`** : chaque entrée d'`alertes` gagne
  `cible_type` (`'controle'` ou `'contrat'`) et `cible_pk`. Le moteur reste
  agnostique de toute route Django — il expose l'identité de l'objet, pas
  une URL (principe posé par le DT, pour garder le moteur réutilisable par
  un autre écran/API/mobile futur).
- **`Templates/registre/dashboard.html`** : le lien de chaque ligne de
  « Mes 5 actions prioritaires » devient conditionnel selon `cible_type`
  (`modifier_controle` / `modifier_contrat`), avec repli sur
  `detail_etablissement` si `cible_type` est absent.
- **`registre/tests.py`** : 3 tests ajoutés —
  `test_alerte_retard_porte_la_cible_controle`,
  `test_alerte_contrat_porte_la_cible_contrat` (moteur),
  `test_action_prioritaire_ouvre_directement_la_fiche_controle` (rendu HTML
  de `dashboard()`, vérifie que le lien vers `modifier_controle` est bien
  présent dans la page).

## 3. Ce qui n'a pas changé

- `registre/views.py` : aucune modification. `tableau_de_bord()` (admin/
  responsable) consomme toujours `collecter_conformite()['alertes']` ;
  les nouvelles clés s'ajoutent au dict sans effet sur son usage actuel.
- Le bloc « Échéances proches » (compteurs) : hors périmètre, le backlog
  n'exige la navigation directe que pour le widget « Mes prochaines
  actions ».
- Aucune nouvelle règle métier, aucun nouveau contrôle de périmètre :
  `modifier_controle`/`modifier_contrat` appliquent déjà leur propre
  vérification, et le Directeur ne reçoit d'alertes que sur son périmètre
  déjà scopé en amont.

## 4. État des 4 Feux Verts

| Feu | État |
|---|---|
| Développement | ✅ Fait |
| Tests | ✅ 156/156 verts (156 = 153 avant ce lot + 3 nouveaux) |
| Documentation | ✅ Ce compte-rendu + document d'architecture |
| Commit Git | en attente |

---

*Rédigé par le Lead Developer PSM2S, 05/07/2026.*
