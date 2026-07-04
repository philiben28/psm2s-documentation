# Revue d'architecture — Lot C1 : mise en service de `DEBUG=False`

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 03/07/2026
Nature : **revue / plan uniquement** (aucun code). C1 n'est plus une correction isolée : c'est la **mise en service** de l'architecture de production préparée par INFRA-1, C2 et C3.

---

## 1. Le mécanisme (déjà en place depuis INFRA-1)

`config/settings.py` :
```
DEBUG = get_env_bool('DJANGO_DEBUG', default=False)
```
- `DJANGO_DEBUG` **présente et vraie** (`true/1/yes/on`) → `DEBUG=True`.
- `DJANGO_DEBUG` **absente**, vide, ou toute autre valeur → `DEBUG=False` (défaut sûr).

Tant que la variable est **présente et à `True`**, le comportement est **identique** à aujourd'hui : le mécanisme n'a rien changé au runtime (démontré par INFRA-1, 94 tests verts, puis 111 aujourd'hui). C1 **n'ajoute pas** de code de configuration — il **active** l'état cible.

## 2. Le basculement (ce qui change concrètement)

Lorsque, en production, `DJANGO_DEBUG` est **supprimée** (ou mise à `False`) :

| Aspect | `DEBUG=True` (avant) | `DEBUG=False` (cible) |
|---|---|---|
| Pages d'erreur | Traceback Django détaillé (chemins, code, settings, variables) | Page 404/500 sobre, **aucune** information technique |
| `ALLOWED_HOSTS` | Non contraignant | **Contrôlé** (déjà correctement renseigné → aucun impact) |
| Desserte statique via `static(STATIC_URL,…)` | Servie par Django | Renvoie `[]` → **servie par Apache** (`collectstatic`) |
| Desserte média | (déjà via `media_protegee` depuis C3) | **inchangée** — voir §3 |

Le seul changement **visible et voulu** : plus aucun traceback exposé.

## 3. Les impacts — démonstration : `DEBUG` ⟂ desserte des médias (après C3)

Avant C3, `/media` était servi par `static(settings.MEDIA_URL, …)` dans `config/urls.py`, **conditionné à `DEBUG=True`** (le helper `static()` ne renvoie des routes que si `DEBUG`). Couper `DEBUG` **aurait cassé** les médias.

Depuis **C3-1**, cette ligne a été **retirée** et remplacée par :
```
path('media/<path:chemin>', registre_views.media_protegee, name='media_protegee')
```
C'est une **route normale**, présente inconditionnellement dans `urlpatterns`, **non gouvernée par `DEBUG`**. Donc `media_protegee` sert les fichiers **que `DEBUG` soit True ou False**.

Preuve empirique : la suite de tests s'exécute avec `DEBUG=False` (comportement natif du lanceur de tests Django) et les **111 tests**, dont ceux de la desserte média (C3-1/C3-2), sont **verts**. Autrement dit, la desserte des médias fonctionne déjà en conditions `DEBUG=False`.

**Conclusion** : après C3, il n'existe plus **aucune** dépendance fonctionnelle entre `DEBUG` et la desserte des médias. Le basculement C1 est donc sûr de ce point de vue.

Reste, côté **statique** (`/static/`), une dépendance à traiter au déploiement : en prod, le statique doit être servi par **Apache** après `collectstatic` (décision d'architecture v1). C'est un point **opérationnel** de déploiement, pas une dépendance de code.

## 4. Le déploiement sur o2switch (procédure précise)

Ordre des opérations (à intégrer à la procédure officielle `DEPLOIEMENT_o2switch.md`) :

1. **Pré-requis** : `DJANGO_SECRET_KEY` déjà posée (C2). Ne **pas** définir `DJANGO_DEBUG` (défaut sûr `False`) — ou la mettre explicitement à `False`.
2. **Déployer** le code (git pull / mise à jour des fichiers).
3. `python manage.py collectstatic --noinput` → alimente `STATIC_ROOT` ; vérifier qu'Apache sert bien `/static/`.
4. `python manage.py migrate` (aucune migration attendue pour C1, mais étape systématique).
5. **`python manage.py check --deploy`** → vérifier l'absence de **`security.W018`** (« DEBUG=True en déploiement »). *(Voir la note ci-dessous sur les autres avertissements.)*
6. **Redémarrer** l'application Passenger (`touch tmp/restart.txt` ou équivalent cPanel).
7. Dérouler la **checklist post-déploiement** (§6 de `DEPLOIEMENT_o2switch.md`).

> **Note importante sur `check --deploy`** : cette commande signale aussi des points relevant de **E4** (cookies `Secure`, HSTS, redirection SSL — W012, W016, W004, W008…). Ces avertissements **subsisteront après C1** et seront levés au lot **E4**. La **barrière propre à C1** est donc ciblée : **absence de `security.W018` (DEBUG)**. La verte complète de `check --deploy` est l'objectif de fin de Phase 2 (après E4).

## 5. Les tests

**Automatisés**
- Suite complète `python manage.py test registre` → **111 tests** verts (déjà exécutés en `DEBUG=False`, donc représentatifs de la cible). C1 n'introduit pas de régression de code.
- (Optionnel, si un test dédié est souhaité) : un test vérifiant que `settings.DEBUG` vaut `False` lorsque `DJANGO_DEBUG` est absente — mais le lanceur force déjà `DEBUG=False`, donc ce test aurait une valeur surtout documentaire.

**Manuels (en préproduction, `DEBUG=False`)**
- **Absence de traceback** : provoquer une erreur (URL inexistante, puis une vue en erreur contrôlée) → vérifier une page **404/500 sobre**, sans stack trace ni settings.
- **Rendu CSS / statiques** : ouvrir le tableau de bord, le calendrier, une fiche établissement → vérifier que le CSS, les icônes (Tabler) et les fichiers statiques se chargent (servis par Apache après `collectstatic`).
- **Médias** : télécharger un document (attachment) et afficher une signature autorisée (inline) → OK ; tenter un média hors périmètre → 404.
- **Parcours nominal** : connexion, navigation, aucune dégradation.
- **`check --deploy`** : W018 absent.

**Pages 404/500** : à défaut de `404.html` / `500.html` personnalisés, Django sert ses pages par défaut (sobres, sans traceback) — acceptable. Leur personnalisation éventuelle est hors périmètre C1 (amélioration cosmétique).

## 6. Plan de retour arrière (rollback)

Objectif : pouvoir revenir **temporairement** à l'état précédent en cas de problème après bascule, le temps d'analyser — **sans redéploiement de code**.

Procédure :
1. Dans cPanel (application Passenger), **définir `DJANGO_DEBUG=True`**.
2. **Redémarrer** l'application Passenger.
3. `DEBUG` repasse à `True` → comportement d'avant bascule rétabli (desserte média inchangée car indépendante de `DEBUG`, seule change la verbosité des erreurs et la desserte statique via `static()`).
4. **Analyser** le problème (logs, `check`, reproduction en préproduction).
5. Corriger, retester, puis **retirer** `DJANGO_DEBUG` pour revenir à l'état sûr.

⚠ Le rollback via `DJANGO_DEBUG=True` **réexpose les tracebacks** : il doit rester **exceptionnel et bref**, strictement le temps du diagnostic, jamais un état durable. La cause racine doit être corrigée pour revenir à `DEBUG=False` au plus vite.

Rollback de code complet (si nécessaire) : `git revert` du commit C1 (mais C1 ne modifiant quasiment pas de code, le levier réel est la variable d'environnement).

## 7. Périmètre code de C1

Très réduit. Le mécanisme existe déjà (INFRA-1). C1 consiste surtout à :
- **documenter** la mise en service et le rollback (procédure officielle) ;
- éventuellement un **nettoyage mineur** de `settings.py` (commentaire) ou l'ajout d'un test documentaire ;
- **aucune** dépendance média (démontré §3), **aucune** migration.

La vraie « livraison » de C1 est **opérationnelle** : variables d'environnement + `collectstatic` + `check --deploy` + checklist + rollback documenté.

## 8. Position de production

Après C1 : la plateforme tourne en **mode production sécurisé** (pas de traceback, secrets externalisés, médias protégés, statique servi par Apache). Il ne restera que **E4** (cookies/transport) pour lever les derniers avertissements `check --deploy` et clore la Phase 2.

---

## Décisions / confirmations attendues du DT

1. **Barrière `check --deploy`** : valides-tu que la barrière **spécifique à C1** est « absence de `security.W018` », les autres avertissements (cookies/HSTS) étant explicitement du ressort de **E4** ?
2. **Pages 404/500** : on conserve les pages **par défaut** de Django pour C1 (sobres, sans traceback), personnalisation éventuelle hors périmètre — d'accord ?
3. **Contenu code de C1** : acceptes-tu que C1 soit essentiellement **opérationnel + documentaire** (le mécanisme étant déjà livré par INFRA-1), avec au plus un nettoyage mineur et/ou un test documentaire ?
