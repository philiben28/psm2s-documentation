# Lot C1 — Mise en service `DEBUG=False` : document de preuve

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 03/07/2026
Nature : lot **opérationnel + documentaire** (mécanisme livré par INFRA-1). Document de preuve de l'absence de mode debug en production.

---

## 1. Objet et périmètre

C1 n'est pas une correction isolée : c'est la **mise en service** de l'état de production préparé par INFRA-1 (mécanisme), C2 (secret externalisé) et C3 (médias protégés). Objectif : `DEBUG=False` en production, sans dépendance résiduelle, avec preuve et procédure de rollback.

## 2. Preuve n°1 — Mécanisme (`config/settings.py`)

Extrait de `config/settings.py` (section SÉCURITÉ) :
```python
DEBUG = get_env_bool('DJANGO_DEBUG', default=False)
```
- Défaut **sûr** : en l'absence de `DJANGO_DEBUG`, `DEBUG` vaut **`False`**.
- La production **ne définit pas** `DJANGO_DEBUG` → `DEBUG=False` par construction.
- Aucun secret ni valeur de debug codés en dur (voir aussi C2 pour `SECRET_KEY`).

Helper (`config/env.py`) : `get_env_bool` renvoie `True` uniquement pour
`true/1/yes/on` ; toute absence ou autre valeur → `False`. Testé (INFRA-1,
`EnvHelperTests`).

## 3. Preuve n°2 — Absence de dépendance `DEBUG` ↔ desserte des médias

Depuis C3-1, `config/urls.py` ne contient plus `static(settings.MEDIA_URL, …)`
(qui n'était actif qu'avec `DEBUG=True`) ; `/media` est servi par une route
**inconditionnelle** :
```python
path('media/<path:chemin>', registre_views.media_protegee, name='media_protegee')
```
Cette route ne dépend pas de `DEBUG`. Preuve empirique : la suite de tests
s'exécute nativement avec `DEBUG=False` et les **111 tests** (dont ceux de la
desserte média C3-1/C3-2) sont **verts**. → La desserte des médias fonctionne
déjà en conditions `DEBUG=False`.

## 4. Preuve n°3 — `check --deploy` (à joindre)

Commande à exécuter en local (avec `DJANGO_SECRET_KEY` posée et **sans**
`DJANGO_DEBUG`, pour refléter la production) :
```
python manage.py check --deploy
```
**Attendu** : **`security.W018` ABSENT**.

**Sortie réelle (03/07/2026)** :
```
System check identified some issues:
WARNINGS:
?: (security.W004) ... SECURE_HSTS_SECONDS ...
?: (security.W008) ... SECURE_SSL_REDIRECT ...
?: (security.W009) ... SECRET_KEY has less than 50 characters ...
?: (security.W012) ... SESSION_COOKIE_SECURE ...
?: (security.W016) ... CSRF_COOKIE_SECURE ...
System check identified 5 issues (0 silenced).
```

**Analyse — `security.W018` est ABSENT → barrière C1 FRANCHIE (`DEBUG=False` confirmé).**

Les 5 avertissements restants ne concernent pas C1 :

| Code | Sujet | Statut / ressort |
|---|---|---|
| W004 | HSTS non défini | **E4** |
| W008 | Redirection SSL | **E4** |
| W012 | `SESSION_COOKIE_SECURE` | **E4** |
| W016 | `CSRF_COOKIE_SECURE` | **E4** |
| W009 | `SECRET_KEY` faible (< 50 car.) | **Artefact local** : dû à la clé de **développement** courte posée dans le shell (`une-cle-de-dev-…`, < 50 caractères). **N'existe pas en production** : la clé de prod, générée par rotation (C2) via `get_random_secret_key()`, fait 50+ caractères à forte entropie. Non-problème en production. |

Conclusion : **C1 est validé** — aucun `W018`. Les points E4 (W004/W008/W012/W016) seront levés au dernier lot de la Phase 2. W009 disparaît en production avec la vraie clé (C2).

## 5. Procédure de mise en service (o2switch)

Voir `DEPLOIEMENT_o2switch.md` §3 quater. Rappel de l'ordre :
secret présent → déploiement → `collectstatic` → `migrate` → `check --deploy`
(W018 absent) → redémarrage Passenger → checklist post-déploiement.

## 6. Plan de rollback (documenté)

Voir `DEPLOIEMENT_o2switch.md` §3 quater. Résumé : poser `DJANGO_DEBUG=True` en
cPanel + redémarrer Passenger → retour immédiat à l'état précédent (sans
redéploiement). **Exceptionnel et bref** (réexpose les tracebacks) ; corriger la
cause racine puis retirer la variable pour revenir à `DEBUG=False`.

## 7. Tests

**Automatisés** : `python manage.py test registre` → **111 tests** verts, exécutés
en `DEBUG=False` (représentatif de la cible). C1 n'introduit aucune régression.

**Manuels (préproduction, `DEBUG=False`)** :
- Absence de traceback : provoquer une erreur → page 404/500 sobre.
- Rendu CSS / statiques : dashboard, calendrier, fiche établissement → OK
  (statique servi par Apache après `collectstatic`).
- Médias : document (attachment) et signature autorisée (inline) → OK ;
  média hors périmètre → 404.
- Parcours nominal : connexion, navigation → aucune dégradation.

## 8. Fichiers modifiés par C1

| Fichier | Nature |
|---|---|
| `config/settings.py` | Commentaire de **mise en service** (marquage C1) — aucun changement de comportement. |
| `Documentation/DEPLOIEMENT_o2switch.md` | Section « Mise en service `DEBUG=False` (C1) » + rollback. |
| `CHANGELOG.md` | Entrée C1. |
| `Documentation/Audits/2026-07-03_C1_Document_de_Preuve.md` | Ce document. |

Aucun modèle, migration, template, ni changement de comportement runtime.

## 9. Disponibilité pour revue

Prêt. **Action attendue de ta part** : exécuter
`python manage.py check --deploy` (avec `DJANGO_SECRET_KEY`, sans `DJANGO_DEBUG`)
et me coller la sortie, pour compléter la **Preuve n°3** (W018 absent). Ensuite,
commit de C1 (`config/settings.py`) puis mise en service serveur selon la procédure.
