# Compte-rendu de développement — Lot C4-6 : correction IDOR (Registre d'Accessibilité)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Protocole PSM2S : étapes 5 (dev), 6 (tests), 7 (doc). En attente 8-10.

---

## 1. Résumé

Sécurisation IDOR des **8 vues du module Registre Public d'Accessibilité**, avec le helper `get_etablissement_ou_404` et la primitive `verifier_acces_etablissement`. Aucun modèle, migration, URL ou logique métier modifié ; aucune fonction ajoutée à `permissions.py`.

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/views.py` | **8 vues** sécurisées (1 à 2 lignes chacune). |
| `registre/tests.py` | **9 tests** ajoutés (`AccessibiliteAccesTests` + base `BaseAccesAccessibilite`). |
| `CHANGELOG.md` | Entrée C4-6. |
| `Documentation/Audits/2026-07-02_C4-6_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_C4-6_IDOR/`.

## 3. Vues sécurisées

| Vue | Contrôle d'objet |
|---|---|
| `accessibilite_detail(etab_pk)` | `get_etablissement_ou_404(user, etab_pk, actif=False)` |
| `accessibilite_grille(etab_pk)` | idem |
| `accessibilite_formation_ajouter(etab_pk)` | idem |
| `accessibilite_piece_ajouter(etab_pk)` | idem |
| `accessibilite_action_ajouter(etab_pk)` | idem |
| `accessibilite_imprimer(etab_pk)` | idem |
| `accessibilite_signer(etab_pk)` | idem (vérifié **avant** la logique de signature) |
| `accessibilite_creer_ticket(action_pk)` | `verifier_acces_etablissement(user, action.registre.etablissement_id)` |

Note : `actif=False` conserve exactement le comportement d'origine (ces vues ne filtraient pas sur `actif`). Chaîne de remontée : `RegistreAccessibilite → etablissement` (OneToOne), `ActionMiseConformite → registre → etablissement`.

## 4. Point mineur signalé (hors périmètre)

`accessibilite_action_ajouter` récupère une zone optionnelle via `?zone=<pk>` (`get_object_or_404(EvaluationZone, pk=zone_pk)`) sans vérifier qu'elle appartient au registre de l'établissement courant. L'établissement (`etab_pk`) étant désormais contrôlé, il n'y a pas de fuite inter-établissements en lecture ; il subsiste au pire un risque d'intégrité (lier une action à une zone d'un autre registre via un paramètre forgé). Faible sévérité, à traiter éventuellement dans un lot d'affinage — non inclus ici pour rester strictement additif.

## 5. Résultats des tests

> **Exécutés et validés le 02/07/2026** (Python 3.13).

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 81 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................................................................................
----------------------------------------------------------------------
Ran 81 tests in 150.887s
OK
Destroying test database for alias 'default'...
```

**Résultat : 81 tests exécutés (72 précédents + 9 C4-6), 0 échec, 0 erreur (OK).**

Chaque test compare, pour un directeur rattaché au site A : accès à l'objet du site A vs site B. Codes attendus : **200 / 404** pour les vues de rendu ; **302 / 404** pour `accessibilite_signer` et `accessibilite_creer_ticket` (accès autorisé → redirection, hors périmètre → 404). Un test vérifie l'accès total de l'admin.

## 6. Analyse du risque de régression

- Surface : 8 vues, 1-2 lignes chacune, aucune fonction existante altérée.
- Périmètre = source unique de vérité (`_get_etab_ids_autorises`).
- Aucun changement de comportement pour les utilisateurs légitimes.
- Migrations : aucune.

## 7. État du chantier

Restant : **Bâtiments** (cas simple, lot court), **mini-lot formulaires** (`nouveau_ticket`, `nouvelle_intervention`). Le gros de la surface IDOR est couvert.

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : lancer `python manage.py check` et `python manage.py test registre` (attendu : **81 OK**) et me transmettre la sortie. Aucun commit effectué.
