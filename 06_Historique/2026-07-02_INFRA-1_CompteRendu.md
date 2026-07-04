# Compte-rendu — Lot INFRA-1 : Préparation de l'environnement de production

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : **lot d'infrastructure** (ne corrige aucune vulnérabilité). Premier lot de la Phase 2, support de l'Architecture de Production v1.

---

## 1. Objectif

Mettre en place la **plomberie de configuration** (variables d'environnement) et l'**hygiène du dépôt**, **sans changer le comportement de la production** et **sans corriger de vulnérabilité**. Prépare C2, C3, C1, E4.

Principe appliqué (correction du DT) : le code livré est déjà **conforme à l'architecture cible** — défaut **sûr `False`** pour `DEBUG` — mais l'**activation** en production est différée au lot C1. Distinction **préparer / activer**.

## 2. Fichiers livrés / modifiés

| Fichier | Nature |
|---|---|
| `config/env.py` | **Nouveau** — helpers `get_env`, `get_env_bool` (défauts sûrs). |
| `config/settings.py` | `DEBUG = get_env_bool('DJANGO_DEBUG', default=False)` ; import du helper ; commentaires C1/C2. |
| `.gitignore` | Durci (ajout `staticfiles/`, `db_formation.sqlite3`, `*.sqlite3`, `.env`). |
| `Documentation/DEPLOIEMENT_o2switch.md` | **Nouveau** — variables d'env, transition préparer/activer, dev local. |
| `registre/tests.py` | **4 tests** ajoutés (`EnvHelperTests`). |
| `CHANGELOG.md` | Entrée INFRA-1. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_INFRA-1/settings_haut.py.bak`.

## 3. Conformité à l'Architecture de Production v1

- **§4.1** (config & secrets) : mécanisme env introduit, défaut sûr → **conforme**.
- **Secure-by-default** : `DEBUG` absent d'env → `False`. Respecté.
- **Séparation données/code** : `.gitignore` durci (statique collecté, bases).
- Ce qui reste hors INFRA-1 (par séquencement) : `SECRET_KEY` (C2), médias/statique (C3), bascule prod DEBUG (C1), cookies/HSTS (E4).

## 4. Point de vigilance — préparer ≠ activer

Le défaut `False` **ne doit pas** être déployé « brut » en production avant C1/C3 : cela couperait la desserte `static()` de `/static/` et `/media/`. La stratégie de transition est documentée (`DEPLOIEMENT_o2switch.md` §2) : soit ne pas déployer INFRA-1 seul en prod, soit poser temporairement `DJANGO_DEBUG=True` côté serveur jusqu'à C1. **Aucune variable de production n'a été modifiée par ce lot.**

Impact **développement local** (assumé) : `DEBUG` par défaut `False` ; poser `DJANGO_DEBUG=True` pour le mode debug (documenté).

## 5. Résultats des tests

> **Exécutés et validés le 02/07/2026** (Python 3.13).

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 94 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..............................................................................................
----------------------------------------------------------------------
Ran 94 tests in 156.785s
OK
Destroying test database for alias 'default'...
```

**Résultat : 94 tests exécutés (90 précédents + 4 INFRA-1), 0 échec, 0 erreur (OK).**
Confirmation empirique de la neutralité : la suite tourne en `DEBUG=False` et les 90 tests existants restent verts. Les 4 nouveaux tests valident le parsing (`get_env_bool` : absent→défaut, valeurs vraies/fausses ; `get_env`).

## 6. Risque de régression

- **Code** : très faible. Mécanisme neutre ; défaut sûr ; aucun secret déplacé (C2), aucune desserte modifiée (C3).
- **Production** : nul — aucune variable serveur touchée, aucun déploiement d'activation.
- **Dev local** : changement assumé et documenté (opt-in `DJANGO_DEBUG=True`).
- Migrations : aucune.

## 7. Suite

Prochain lot du séquencement validé : **C2 — migration de `SECRET_KEY`** (retrait du fallback, sortie du secret des `passenger_wsgi*`, rotation). Autonome, faible risque.

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : lancer `python manage.py check` et `python manage.py test registre` (attendu : **94 OK**) et me transmettre la sortie. Aucun commit effectué.
