# Compte-rendu de développement — Lot C4-2 : correction IDOR (module Contrôles)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Protocole PSM2S : étapes 5 (dev), 6 (tests), 7 (doc). En attente 8-10 (revue DT, validation, commit).

---

## 1. Résumé

Extension de la correction IDOR (C4) au **module Contrôles**, en réutilisant intégralement la primitive livrée au Lot C4-1. Un utilisateur au périmètre restreint ne peut plus accéder à un contrôle rattaché à un établissement hors de son périmètre via l'identifiant d'URL. Aucun modèle, migration, URL ni logique métier modifié ; aucun refactoring ; aucune nouvelle fonction dans `permissions.py`.

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/views.py` | Import de `verifier_acces_etablissement` ; **4 vues** sécurisées (1 ligne ajoutée chacune, sauf `nouveau_controle` : `get_object_or_404(Etablissement…)` → `get_etablissement_ou_404`). |
| `registre/tests.py` | **12 tests** ajoutés (classes `ModifierControleTests`, `HistoriqueControleTests`, `NouvelleRealisationTests`, `NouveauControleTests` + base `BaseAccesControle`). |
| `CHANGELOG.md` | Entrée C4-2. |
| `Documentation/Audits/2026-07-02_C4-2_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_C4-2_IDOR/views_controles_extrait.py.bak`.

## 3. Vues sécurisées et technique employée

| Vue | Décorateur de rôle | Contrôle d'objet ajouté |
|---|---|---|
| `nouveau_controle(etab_pk)` | `@gestionnaire_requis` | `get_etablissement_ou_404(request.user, etab_pk)` (objet = Établissement) |
| `modifier_controle(pk)` | `@gestionnaire_requis` | `verifier_acces_etablissement(request.user, etab.pk)` |
| `nouvelle_realisation(controle_pk)` | `@factotum_niveau_requis(2)` | `verifier_acces_etablissement(request.user, controle.etablissement_id)` |
| `historique_controle(controle_pk)` | `@login_required` | `verifier_acces_etablissement(request.user, controle.etablissement_id)` |

Motif retenu pour les objets enfants : récupérer l'objet (`get_object_or_404`), puis appeler la primitive `verifier_acces_etablissement` sur son `etablissement_id`. Aucune abstraction nouvelle introduite — conforme à la consigne « pas de refactoring » et à la décision DT de réutiliser la primitive C4-1. (Une éventuelle aide générique `get_objet_ou_404(model, pk, chemin_etablissement)` reste à valider par le DT si la répétition le justifie sur les lots suivants.)

## 4. Résultats des tests

> **Exécutés et validés le 02/07/2026** dans l'environnement PSM2S (Python 3.13), le bac à sable de session étant indisponible.

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 29 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.............................
----------------------------------------------------------------------
Ran 29 tests in 63.559s
OK
Destroying test database for alias 'default'...
```

**Résultat : 29 tests exécutés (17 C4-1 + 12 C4-2), 0 échec, 0 erreur (OK).**

| Classe (C4-2) | Attendu |
|---|---|
| `ModifierControleTests` | directeur : 200 sur son site, 404 sur l'autre ; admin : 200 partout |
| `HistoriqueControleTests` | directeur : 200 / 404 ; factotum via ticket : 200 (A) / 404 (B) |
| `NouvelleRealisationTests` | directeur : 200 / 404 ; factotum via ticket : 200 (A) / 404 (B) |
| `NouveauControleTests` | directeur : 200 sur son site, 404 sur l'autre ; admin : 200 partout |

## 5. Analyse du risque de régression

- **Surface minime** : 4 vues, 1 ligne ajoutée chacune, aucune fonction existante altérée.
- **Périmètre = source unique de vérité** (`_get_etab_ids_autorises` via la primitive) → cohérence garantie avec les listes et avec le module Établissement (C4-1). Risque de sur-restriction faible, couvert par les tests.
- **Aucun changement de comportement** pour les utilisateurs légitimes (contrairement à C4-1, il n'y avait ici aucune redirection préexistante à remplacer : l'accès était simplement non contrôlé).
- **`nouvelle_realisation`** reste protégée au niveau rôle par `@factotum_niveau_requis(2)` ; le contrôle d'objet s'ajoute par-dessus sans modifier ce garde-fou.
- Migrations : aucune.

## 6. Recommandations pour le Lot C4-3

- Cible proposée : **Documents + Tickets + Interventions** (objets à forte fréquence d'accès et de suppression), avec la même primitive. Attention aux **suppressions de fichiers physiques** : vérifier l'accès avant tout `delete()`.
- Filtrer le `queryset` de `InterventionForm` (menu déroulant listant les tickets de tous les sites).
- Bâtiments (`nouveau_batiment`, `modifier_batiment`, `supprimer_batiment`) : lot dédié court.
- DUERP / Accessibilité : traiter en dernier, avec correction de l'incohérence **E5** (`peut_tout_voir`).

## 7. Disponibilité pour revue

Développement et documentation terminés. **Avant validation finale et commit**, merci de lancer `python manage.py check` et `python manage.py test registre` et de me transmettre la sortie (résultat attendu : 29 tests OK). Aucun commit n'a été effectué (étape 10, après validation).
