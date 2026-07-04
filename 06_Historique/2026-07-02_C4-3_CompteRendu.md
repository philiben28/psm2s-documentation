# Compte-rendu de développement — Lot C4-3 : correction IDOR (Documents, Tickets, Interventions)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Protocole PSM2S : étapes 5 (dev), 6 (tests), 7 (doc). En attente 8-10.

---

## 1. Résumé

Extension de la correction IDOR aux modules **Documents, Tickets (+ pièces jointes) et Interventions**, avec la primitive `verifier_acces_etablissement` (aucune nouvelle fonction dans `permissions.py`). Point de vigilance spécifique respecté : la vérification d'accès est placée **avant toute suppression de fichier physique**. Aucun modèle, migration, URL ni logique métier modifié ; aucun refactoring.

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/views.py` | **8 vues** sécurisées (1 à 2 lignes chacune). |
| `registre/tests.py` | **10 tests** ajoutés (`DocumentAccesTests`, `TicketAccesTests`, `InterventionAccesTests` + base `BaseAccesContenu`). |
| `CHANGELOG.md` | Entrée C4-3. |
| `Documentation/Audits/2026-07-02_C4-3_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_C4-3_IDOR/`.

## 3. Vues sécurisées

| Vue | Décorateur | Contrôle d'objet |
|---|---|---|
| `nouveau_document(etab_pk)` | `@login_required` | `get_etablissement_ou_404(user, etab_pk)` |
| `modifier_document(pk)` | `@login_required` | `verifier_acces_etablissement(user, doc.controle.etablissement_id)` |
| `supprimer_document(pk)` | `@login_required` | idem, **avant** suppression fichier |
| `modifier_ticket(pk)` | `@factotum_niveau_requis(2)` | `verifier_acces_etablissement(user, ticket.etablissement_id)` |
| `supprimer_ticket(pk)` | `@acces_requis(admin,resp,dir)` | idem, **avant** suppression |
| `ajouter_piece_jointe(ticket_pk)` | `@login_required` | `verifier_acces_etablissement(user, ticket.etablissement_id)` |
| `supprimer_piece_jointe(pk)` | `@login_required` | `verifier_acces_etablissement(user, pj.ticket.etablissement_id)`, **avant** suppression |
| `modifier_intervention(pk)` | `@factotum_niveau_requis(2)` | `verifier_acces_etablissement(user, interv.ticket.etablissement_id)` |

Note : `modifier_document`/`supprimer_document` conservent leur garde défensif d'origine (`if etab is not None`) — le contrôle ne s'applique donc que si le document est rattaché à un établissement (cas nominal, `Document.controle` étant obligatoire).

## 4. Résultats des tests

> **Exécutés et validés le 02/07/2026** dans l'environnement PSM2S (Python 3.13).

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 40 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........................................
----------------------------------------------------------------------
Ran 40 tests in 87.945s
OK
Destroying test database for alias 'default'...
```

**Résultat : 40 tests exécutés (29 précédents + 11 C4-3), 0 échec, 0 erreur (OK).**

| Classe (C4-3) | Attendu |
|---|---|
| `DocumentAccesTests` (4) | directeur : 200 sur son site / 404 sur l'autre (nouveau, modifier, supprimer) ; admin : 200 |
| `TicketAccesTests` (4) | directeur : 200 / 404 (modifier, supprimer, ajouter PJ, supprimer PJ) ; admin : 200 |
| `InterventionAccesTests` (2) | directeur : 200 / 404 ; factotum via ticket : 200 (A) / 404 (B) |

## 5. Analyse du risque de régression

- Surface minime (8 vues, 1-2 lignes), aucune fonction existante altérée, périmètre = source unique de vérité.
- Aucun changement de comportement pour les utilisateurs légitimes (aucune redirection préexistante remplacée).
- Suppressions de fichiers : la vérification précède désormais tout `delete()` physique → renforcement sans effet de bord sur le flux nominal.
- Migrations : aucune.

## 6. Suivi identifié (hors périmètre C4-3)

Deux vues de **création par formulaire** exposent une faille voisine (over-posting de l'établissement via un menu déroulant non filtré), qui relève de `forms.py` et non de l'IDOR-par-URL :
- `nouveau_ticket` → `TicketTravauxForm.etablissement` liste tous les établissements actifs.
- `nouvelle_intervention` → `InterventionForm.ticket` liste les tickets de tous les sites (audit F9).

Recommandation : mini-lot dédié « filtrage des formulaires par périmètre » (passage de `user`/`etablissements_autorises` aux formulaires concernés), à valider par le DT car il touche la couche formulaire.

## 7. Recommandations pour le Lot C4-4

- Cible : **Commissions + Contrats + Carnet Eau** (mêmes chemins de remontée vers l'établissement).
- Puis **Bâtiments** (lot court dédié) et **DUERP + Accessibilité** (traiter en dernier avec la correction de l'incohérence E5 `peut_tout_voir`).

## 8. Disponibilité pour revue

Développement et documentation terminés ; tests **40/40 OK** exécutés et validés.

**Traçabilité Git** : le commit `068bb13` (« Securite C4-3… ») regroupe **les modifications de C4-2 et de C4-3**. Le commit intermédiaire de C4-2 n'ayant pas été effectué avant le démarrage de C4-3, le `git add` a capturé les deux lots ensemble. Choix acté (option 1) : historique conservé tel quel, sans réécriture. Le détail par lot reste tracé dans les comptes-rendus C4-2 et C4-3 et dans le CHANGELOG.
