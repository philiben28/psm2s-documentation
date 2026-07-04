# Compte-rendu de développement — Lot C4-4 : correction IDOR (Commissions, Contrats, Carnet Eau)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Protocole PSM2S : étapes 5 (dev), 6 (tests), 7 (doc). En attente 8-10.

---

## 1. Résumé

Extension de la correction IDOR aux modules **Commissions de sécurité, Contrats et Carnet sanitaire Eau** (17 vues), avec la primitive existante `verifier_acces_etablissement` et le helper `get_etablissement_ou_404`. Confirmation de la remarque stratégique du DT : ces trois modules suivent le schéma « objet rattaché à un établissement », la primitive s'applique donc sans nouvelle logique — y compris sur les chaînes de FK profondes (`analyse → point → réseau → établissement`, `action → prescription → visite → établissement`). Aucun modèle, migration, URL ou logique métier modifié ; aucun refactoring ; aucune fonction ajoutée à `permissions.py`.

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/views.py` | **17 vues** sécurisées (1 à 2 lignes chacune). |
| `registre/tests.py` | **17 tests** ajoutés (`CommissionAccesTests`, `ContratAccesTests`, `EauAccesTests` + base `BaseAccesC44`). |
| `CHANGELOG.md` | Entrée C4-4. |
| `Documentation/Audits/2026-07-02_C4-4_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_C4-4_IDOR/`.

## 3. Vues sécurisées et chemins de remontée

**Commissions** (8) : `nouvelle_visite_commission` (etab_pk → helper), `detail_visite_commission`, `modifier_visite_commission`, `supprimer_visite_commission` (via `visite.etablissement_id`), `nouvelle_prescription` (via `visite.etablissement_id`), `modifier_prescription` (via `prescription.visite.etablissement_id`), `nouvelle_action_prescription` (via `visite`), `supprimer_action_prescription` (via `action.prescription.visite.etablissement_id`).

**Contrats** (3) : `nouveau_contrat` (etab_pk → helper), `modifier_contrat`, `supprimer_contrat` (via `contrat.etablissement_id`).

**Carnet Eau** (6) : `carnet_eau`, `nouveau_reseau_eau`, `nouvelle_analyse_eau` (etab_pk → helper), `nouveau_point_prelevement` (via `reseau.etablissement_id`), `modifier_analyse_eau`, `supprimer_analyse_eau` (via `analyse.point.reseau.etablissement_id`).

Pour les 5 vues `supprimer_*` du lot, la vérification d'accès est placée **avant** toute suppression de fichier physique. Pour `supprimer_visite_commission` (`@admin_requis`), le contrôle d'objet est un no-op (l'admin a un accès total) mais il est ajouté par cohérence et défense en profondeur.

## 4. Résultats des tests

> **Exécutés et validés le 02/07/2026** dans l'environnement PSM2S (Python 3.13).

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 57 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 117.320s
OK
Destroying test database for alias 'default'...
```

**Résultat : 57 tests exécutés (40 précédents + 17 C4-4), 0 échec, 0 erreur (OK).**

Chaque test vérifie, pour un directeur rattaché au site A : accès **200** à l'objet de son site, **404** à l'objet du site B. Cas particulier `supprimer_visite_commission` (`@admin_requis`) : directeur **302** (bloqué au rôle), admin **200**.

## 5. Analyse du risque de régression

- Surface : 17 vues, 1-2 lignes chacune, aucune fonction existante altérée.
- Périmètre = source unique de vérité (`_get_etab_ids_autorises`), cohérent avec les lots C4-1 à C4-3.
- Aucun changement de comportement pour les utilisateurs légitimes.
- Suppressions de fichiers : vérification désormais **avant** tout `delete()`.
- Migrations : aucune.

## 6. État global du chantier C4

| Lot | Périmètre | Vues | Tests cumulés |
|---|---|---|---|
| C4-1 | Établissement | 3 | 17 |
| C4-2 | Contrôles | 4 | 29 |
| C4-3 | Documents, Tickets, Interventions | 8 | 40 |
| C4-4 | Commissions, Contrats, Eau | 17 | 57 |
| **Total** | | **32 vues** | **57 tests** |

Restant : **DUERP** (+ correction E5 `peut_tout_voir`), **Accessibilité**, **Bâtiments** (cas simple, lot court), et le **mini-lot formulaires** (`nouveau_ticket`, `nouvelle_intervention`).

## 7. Recommandations pour le Lot C4-5

- Cible proposée : **DUERP**, en intégrant la correction de l'incohérence **E5** — aligner `peut_tout_voir`/`peut_voir_etablissement` sur `_get_etab_ids_autorises` et sécuriser `duerp_liste`, `duerp_detail`, `duerp_checklist`, `duerp_plan_action`, `duerp_action_*`, `duerp_modifier`, `duerp_imprimer`, `duerp_signer`, `duerp_supprimer_signature`.
- Attention aux vues de **signature** (`duerp_signer`) qui possèdent déjà une logique `DroitSignature.peut_signer` : combiner sans doublon.

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : lancer `python manage.py check` et `python manage.py test registre` (attendu : 57 OK) et me transmettre la sortie. Aucun commit effectué.
