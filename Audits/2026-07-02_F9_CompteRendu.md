# Compte-rendu de développement — Lot F9 : FORM-PERIMETRE (filtrage des formulaires)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : **nouvelle phase** — prévention en amont des créations hors périmètre. Distincte du contrôle d'accès IDOR (objets existants).

---

## 1. Résumé

Là où l'IDOR empêchait d'**accéder** à un objet hors périmètre, F9 empêche de le **choisir** (et de le sur-envoyer) à la création/édition. Deux menus déroulants sont désormais filtrés par le périmètre de l'utilisateur :
- `TicketTravauxForm.etablissement`
- `InterventionForm.ticket`

Réutilise `etablissements_autorises` (permissions.py), qui délègue à `_get_etab_ids_autorises` — même source unique de vérité que tout le reste. Aucun modèle, migration ni URL modifié.

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/forms.py` | `TicketTravauxForm.__init__` et `InterventionForm.__init__` : paramètre `user` + filtrage du `queryset`. |
| `registre/views.py` | `nouveau_ticket`, `modifier_ticket`, `nouvelle_intervention` : passage de `user=request.user` aux formulaires (6 instanciations). |
| `registre/tests.py` | **5 tests** ajoutés (`FormPerimetreTests`). |
| `CHANGELOG.md` | Entrée F9. |
| `Documentation/Audits/2026-07-02_Anomalies_Restantes.md` | F9 → « Résolues ». |
| `Documentation/Audits/2026-07-02_F9_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_F9/extrait.py.bak`.

## 3. Mécanisme

Dans chaque formulaire, le `queryset` de départ (inchangé) est restreint **seulement si** un `user` est fourni **et** que son périmètre n'est pas total :

```
ids = etablissements_autorises(user)
if ids is not None:            # None = admin / responsable / superuser → tout
    qs = qs.filter(pk__in=ids)  # ou etablissement_id__in=ids pour les tickets
```

Propriétés :
- **Rétrocompatible** : sans `user`, le comportement d'origine est conservé (aucune régression sur l'admin Django, qui utilise ses propres formulaires).
- **Défense contre l'over-posting** : un `ModelChoiceField` rejette en validation toute valeur hors de son `queryset`. Passer `user` **aussi en POST** garantit qu'un `etablissement`/`ticket` forgé hors périmètre rend le formulaire invalide (pas seulement masqué à l'affichage).
- **Cohérence édition** : sur `modifier_ticket`, l'établissement courant du ticket est nécessairement dans le périmètre (accès déjà contrôlé en C4-3), donc présent dans le `queryset` — pas de faux négatif.

## 4. Résultats des tests

> **Exécutés et validés le 02/07/2026** (Python 3.13).

Sortie réelle :
```
> python manage.py test registre
Found 90 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..........................................................................................
----------------------------------------------------------------------
Ran 90 tests in 170.821s
OK
Destroying test database for alias 'default'...
```

**Résultat : 90 tests exécutés (85 précédents + 5 F9), 0 échec, 0 erreur (OK).**

Tests F9 :
- `test_ticket_form_directeur_limite_aux_sites_autorises` : le déroulant établissement d'un directeur contient son site, pas l'autre.
- `test_ticket_form_admin_voit_tous_les_sites` : admin → tous.
- `test_intervention_form_directeur_limite_aux_tickets_autorises` : déroulant ticket restreint au périmètre.
- `test_intervention_form_admin_voit_tous_les_tickets` : admin → tous.
- `test_over_posting_ticket_hors_perimetre_refuse` : un POST forgé `etablissement=<site B>` par un directeur du site A ne crée **aucun** ticket sur B (formulaire invalide).

## 5. Analyse du risque de régression

- Surface : 2 `__init__` de formulaires + 6 instanciations de vues.
- Filtrage **conditionnel** (`user is not None` et périmètre non total) → aucun impact pour admin/responsable, ni pour l'admin Django.
- Périmètre = source unique de vérité.
- Migrations : aucune.

## 6. État du chantier

Registre — reste une seule entrée ouverte : **ACC-ZONE** (cohérence métier `?zone=<pk>`). Hors registre : points de sécurité production de l'audit initial (DEBUG, SECRET_KEY, médias…), à qualifier en revue quand le DT le souhaitera.

## 7. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : lancer `python manage.py check` et `python manage.py test registre` (attendu : **90 OK**) et me transmettre la sortie. Aucun commit effectué.
