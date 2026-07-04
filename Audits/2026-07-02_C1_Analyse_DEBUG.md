# Analyse — Anomalie C1 : `DEBUG` en production

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : **analyse uniquement**. Aucune modification de code, aucune correction proposée en patch.

---

## 1. Configuration actuelle de `DEBUG` (dev et prod)

Constat vérifié par lecture directe du code :

| Environnement | Module de settings | `DEBUG` |
|---|---|---|
| Production (site principal) | `config/settings.py` (`config.settings`) | **`True`** — `settings.py:17` : `DEBUG = True  # Passer à False en production réelle` |
| Formation (sous-domaine public) | `config/settings_formation.py` | **`True`** — `settings_formation.py:26` : `DEBUG = True` (hérite de `settings.py` puis re-force `True`) |
| Développement local | mêmes modules | **`True`** (identique) |

**Il n'existe aujourd'hui aucune distinction entre dev et prod** : `DEBUG` vaut `True` partout. Le commentaire « Passer à False en production réelle » n'a jamais été appliqué. C'est exactement l'anomalie C1 de l'audit (criticité Critique).

## 2. Comment la valeur est-elle injectée ?

`DEBUG` est une **valeur littérale codée en dur** dans chaque module de settings. Elle **n'est pas** pilotée par variable d'environnement, ni par aucun autre mécanisme.

Ce qui **est** piloté par l'environnement, c'est le **choix du module de settings** (pas la valeur de DEBUG) :
- `passenger_wsgi.py:7` → `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')` (prod principale).
- `passenger_wsgi_formation.py:8` → `config.settings_formation` (formation).
- `manage.py`, `config/wsgi.py`, `config/asgi.py`, `import_excel.py` → `config.settings` par défaut.

À noter (hors périmètre C1, relève de C2) : `SECRET_KEY` est, elle, lue depuis l'environnement (`os.getenv('DJANGO_SECRET_KEY', 'django-insecure-…')`) avec la clé réelle injectée en clair dans les `passenger_wsgi*.py`. Le mécanisme « env » existe donc déjà dans le projet — mais il n'est **pas** utilisé pour `DEBUG`.

## 3. Risques réels subsistant aujourd'hui

`DEBUG=True` sur des domaines publics (`psm2s.pbci-conseils.fr`, `formation.…`) implique concrètement :

- **Divulgation d'informations sensibles** : toute erreur non gérée renvoie une page de traceback Django exposant chemins serveur, extraits de code, variables locales, réglages (`settings`), fragments de requêtes SQL et parfois de données.
- **Exposition indirecte de la configuration** : le contexte de debug facilite la reconnaissance pour un attaquant (versions, structure, noms d'apps).
- **Couplage avec C3 (aggravant)** : c'est précisément `DEBUG=True` qui active la desserte des médias via `static(settings.MEDIA_URL, …)` dans `config/urls.py`. Tant que `DEBUG=True`, les documents confidentiels (`/media/…` : PV, contrats, signatures) restent servis sans authentification. C1 et C3 sont donc liés (voir §5).
- **Absence de garde-fou** : rien n'empêche aujourd'hui un déploiement de partir avec `DEBUG=True` — c'est l'état nominal.

Gravité : **Critique** (confidentialité), sur un périmètre contenant des données à caractère personnel et réglementaire.

## 4. Architecture proposée (pour que `DEBUG=True` ne puisse jamais être activé accidentellement en production)

Principe directeur : **fail-safe / secure-by-default**. La valeur sûre (`False`) doit être celle qu'on obtient **quand on ne fait rien**. L'activation de `DEBUG` doit être un **acte explicite et local**, jamais un défaut.

### Option A — Pilotage par variable d'environnement, défaut `False` (recommandée pour C1)

Principe :
- `DEBUG` n'est plus une constante mais est dérivé d'une variable d'environnement dédiée (ex. `DJANGO_DEBUG`), avec **défaut `False`** :
  `DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'` (lecture stricte).
- **Production** : ne définit **pas** la variable → `DEBUG=False` automatiquement. Aucune action = état sûr.
- **Développement local** : le développeur pose `DJANGO_DEBUG=True` dans son environnement (ou un `.env` non versionné).
- Suppression du littéral `DEBUG = True` dans `settings.py` **et** `settings_formation.py`.

Avantages : minimal (2 lignes), cohérent avec le mécanisme déjà en place pour `SECRET_KEY`, aucun changement d'arborescence, réversible. Le défaut est sûr.

### Option B — Séparation des settings (dev / prod)

Principe : éclater `settings.py` en `settings/base.py`, `settings/dev.py` (`DEBUG=True`), `settings/prod.py` (`DEBUG=False`), et fixer `DJANGO_SETTINGS_MODULE=config.settings.prod` en production.

Avantages : séparation nette, extensible. Inconvénients : refactor plus large (imports, arborescence, tous les `passenger_wsgi*`/`manage.py`/`wsgi`/`asgi`), donc plus de surface de régression — dépasse le périmètre « une anomalie = un lot » de C1.

### Garde-fous complémentaires (indépendants de l'option retenue)

1. **Gate de déploiement** : intégrer `python manage.py check --deploy` à la procédure de mise en production. Ce check émet `security.W018` (« DEBUG=True en déploiement ») ; en le traitant comme **bloquant** (échec du déploiement), on rend l'accident impossible côté process.
2. **Cohérence formation** : `settings_formation` est aussi sur un sous-domaine public → même traitement (défaut `False`, opt-in explicite). À décider par le DT : la formation peut-elle rester en `DEBUG=True` ? Recommandation : non, ou alors via opt-in explicite documenté.
3. **404/500** : avec `DEBUG=False`, prévoir (ou vérifier) des pages `404.html` / `500.html` — sinon Django sert des pages par défaut sobres (acceptable, mais à confirmer).

**Recommandation** : **Option A** pour le lot C1 (minimal, secure-by-default) + garde-fou n°1 (gate `check --deploy`). L'option B pourra être envisagée plus tard si le nombre d'environnements croît.

## 5. Risque de régression

Le risque n'est **pas** dans le code applicatif mais dans les **comportements couplés à `DEBUG`** lors du passage à `False` en production :

- **Desserte statique/médias (couplage fort avec C3)** : `django.conf.urls.static.static()` (dans `config/urls.py`) **ne renvoie des routes que si `DEBUG=True`**. Passer `DEBUG=False` **désactive** la desserte de `/static/` et `/media/` par Django → risque de **CSS/images/documents cassés** si le serveur web (Apache/o2switch + `collectstatic`) et une desserte protégée des médias (objet de C3) ne sont pas en place.
  → **Conclusion clé** : le **basculement effectif de la production** en `DEBUG=False` doit être **coordonné avec C3**. Idéalement, C1 (mécanisme) et C3 (desserte médias/statique) sont **déployés ensemble**, ou C1 introduit le mécanisme pendant que la prod continue d'opter explicitement pour `True` jusqu'à ce que C3 soit prêt (à éviter, car cela laisse la fenêtre ouverte).
- **`ALLOWED_HOSTS`** : déjà correctement renseigné → pas de régression attendue de ce côté (une `DisallowedHost` ne surviendrait que sur un hôte non listé).
- **Pages d'erreur** : bascule vers les pages 404/500 de production au lieu des tracebacks — comportement voulu, à vérifier visuellement.
- **Suite de tests** : le paramètre `DEBUG` n'influence pas les 90 tests actuels (le client de test force son propre contexte). Aucune régression fonctionnelle attendue sur la suite.

Le risque « code » du lot C1 lui-même (Option A) est **faible** : deux lignes de settings. Le risque « déploiement » est **réel et maîtrisable** à condition de séquencer avec C3.

## 6. Plan de tests proposé

**Tests automatisés (unitaires) — logique de parsing**
- `DJANGO_DEBUG` absent → `DEBUG is False` (défaut sûr).
- `DJANGO_DEBUG=True` → `DEBUG is True`.
- `DJANGO_DEBUG=False` / valeur quelconque (`0`, `''`, `true` minuscule si lecture stricte) → `DEBUG is False`.
  (Réalisable via un helper de parsing testable, ou `override_settings` selon l'implémentation retenue.)

**Gate de déploiement**
- `python manage.py check --deploy` exécuté en préproduction : ne doit **pas** signaler `security.W018`. Le traiter comme bloquant dans la procédure.

**Non-régression**
- Suite complète `python manage.py test registre` → **90 tests** toujours verts.

**Vérification manuelle en préproduction (avec `DEBUG=False`)**
- Provoquer une erreur → confirmer l'absence de traceback (page 500 sobre).
- Vérifier le rendu des pages (CSS/statique) **après** mise en place de la desserte statique/médias (jonction C3).
- Vérifier qu'aucun contenu `/media/` n'est plus servi publiquement (objet de C3, à valider conjointement).
- Confirmer un accès nominal (connexion, tableau de bord, calendrier) sans dégradation.

---

## Synthèse pour décision

- **C1 est réel et Critique** : `DEBUG=True` partout, en dur, sans pilotage par environnement.
- **Correctif recommandé** : Option A (env `DJANGO_DEBUG`, défaut `False`) + gate `check --deploy`. Périmètre minimal, secure-by-default.
- **Dépendance à acter** : le **cut-over production** vers `DEBUG=False` est **couplé à C3** (desserte statique/médias). Décision attendue du DT : traiter **C1 et C3 dans une séquence coordonnée** (recommandé), plutôt que C1 seul qui, appliqué en prod sans C3, casserait la desserte des fichiers.
