# Compte-rendu de développement — Lot C4-7 : correction IDOR (module Bâtiments) — CLÔTURE DU CHANTIER IDOR

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Protocole PSM2S : étapes 5 (dev), 6 (tests), 7 (doc). En attente 8-10.

---

## 1. Résumé

Dernier lot IDOR : sécurisation des **3 vues du module Bâtiments**, avec le helper `get_etablissement_ou_404` et la primitive `verifier_acces_etablissement`. Cas le plus simple (remontée directe `batiment.etablissement_id`). Aucun modèle, migration, URL ou logique métier modifié ; aucune fonction ajoutée à `permissions.py`.

**Ce lot clôt le chantier IDOR.**

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/views.py` | **3 vues** sécurisées (1 ligne chacune). |
| `registre/tests.py` | **4 tests** ajoutés (`BatimentAccesTests` + base `BaseAccesBatiment`). |
| `CHANGELOG.md` | Entrée C4-7. |
| `Documentation/Audits/2026-07-02_C4-7_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_C4-7_IDOR/`.

## 3. Vues sécurisées

| Vue | Contrôle d'objet |
|---|---|
| `nouveau_batiment(etab_pk)` | `get_etablissement_ou_404(user, etab_pk)` (actif=True, comportement d'origine) |
| `modifier_batiment(pk)` | `verifier_acces_etablissement(user, batiment.etablissement_id)` |
| `supprimer_batiment(pk)` | idem, **avant** suppression |

## 4. Résultats des tests

> **Exécutés et validés le 02/07/2026** (Python 3.13), après la correction du lot **BUG-TPL-01** dont C4-7 dépend.

Sortie réelle :
```
> python manage.py test registre
Found 85 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.....................................................................................
----------------------------------------------------------------------
Ran 85 tests in 145.557s
OK
Destroying test database for alias 'default'...
```

**Résultat : 85 tests exécutés (81 précédents + 4 C4-7), 0 échec, 0 erreur (OK).**
Le premier passage avait révélé le bug latent BUG-TPL-01 ; après correction, la suite est intégralement verte.

Codes attendus (directeur rattaché au site A) : `nouveau_batiment` 302/404 (GET redirige) ; `modifier_batiment` 200/404 ; `supprimer_batiment` 302/404 ; admin → accès total.

## 5. Analyse du risque de régression

- Surface : 3 vues, 1 ligne chacune. Aucune fonction existante altérée.
- Périmètre = source unique de vérité. Aucun changement de comportement pour les utilisateurs légitimes. Aucune migration.

## 6. Bilan du chantier IDOR (clôturé)

| Lot | Périmètre | Vues |
|---|---|---|
| C4-1 | Établissement | 3 |
| C4-2 | Contrôles | 4 |
| C4-3 | Documents / Tickets / Interventions | 8 |
| C4-4 | Commissions / Contrats / Eau | 17 |
| C4-5 | DUERP | 11 |
| C4-6 | Registre d'Accessibilité | 8 |
| C4-7 | Bâtiments | 3 |
| **Total IDOR** | | **54 vues** |

Lots connexes réalisés en cours de route : **M11** (compat Python) et **E5** (visibilité liste DUERP).
Suite totale : **85 tests**.

**Toutes les vues « objet » de PSM2S rattachées à un établissement sont désormais protégées** par le contrôle d'accès au niveau de l'objet, avec `_get_etab_ids_autorises` comme source unique de vérité et réponse 404 en cas d'accès hors périmètre.

## 7. Suite

Reste hors chantier IDOR (nouvelle phase — prévention en amont) :
- **FORM-PERIMETRE** (registre) : filtrage des menus déroulants de `nouveau_ticket` et `nouvelle_intervention`. Nature différente : « empêcher de choisir » plutôt qu'« empêcher d'accéder ».
- **ACC-ZONE** (registre) : cohérence métier `?zone=<pk>`.

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : lancer `python manage.py check` et `python manage.py test registre` (attendu : **85 OK**) et me transmettre la sortie. Aucun commit effectué.
