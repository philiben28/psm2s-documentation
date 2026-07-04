# Phase 2 — Architecture de production PSM2S (document d'architecture cible)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : **architecture uniquement**. Aucune modification de code. Ce document définit la cible de production dans laquelle s'inscriront les lots C1 (DEBUG), C2 (SECRET_KEY), C3 (médias) et E4 (cookies/transport).

---

## STATUT : ARCHITECTURE DE PRODUCTION **v1 — VALIDÉE** (DT, 02/07/2026)

> **Référence permanente du projet.** Toute évolution future (sécurité, performances, fonctionnalités) doit être **compatible avec cette architecture**, ou **justifier explicitement un écart** en revue. Document opposable au même titre que le protocole de développement et le registre des anomalies.

### Critère de gouvernance (nouveau — DT)
> À partir de maintenant, chaque correction doit répondre à : **« Est-elle conforme à l'architecture cible v1 ? »** Si non, elle n'est pas développée. Ce critère prime, au même titre que la règle « une anomalie = un lot ».

### Décisions arbitrées
1. **Variables d'environnement** : **Passenger (cPanel o2switch)** en production. Pas de `.env` en prod (un `.env` local reste possible en dev, hors architecture cible).
2. **Settings** : **Option A** — un seul `settings.py` piloté par l'environnement. Pas de split.
3. **Statique** : **Apache + `collectstatic`**. Pas de WhiteNoise.
4. **Médias** : approche **progressive** — Étape 1 : **vue Django sécurisée** ; Étape 2 (ultérieure, à vérifier côté Apache/o2switch) : optimisation `X-Sendfile`. On ne complexifie pas d'emblée.
5. **Formation** : **`DEBUG=False`** aussi (aucun sous-domaine public ne doit afficher de tracebacks).
6. **Base de données** : **décision différée** — reste **SQLite** pour l'instant ; sujet non sécuritaire (perf/sauvegarde/maintenance), traité plus tard en chantier **E6**.

### Séquencement validé (révisé par le DT — un objectif par commit)
```
INFRA-1  →  C2 (SECRET_KEY)  →  C3 (médias protégés)  →  C1 (DEBUG=False)  →  E4 (cookies/transport)
```
Note : C1 et E4 restent **deux lots distincts** (pas de fusion), même si E4 prend son plein effet avec `DEBUG=False`. E6 (base de données) et l'optimisation X-Sendfile sont hors de cette séquence.

### Nommage
Le lot préparatoire n'est pas un lot de sécurité mais **d'infrastructure** : **`INFRA-1 — Préparation de l'environnement de production`**. Il ne corrige aucune vulnérabilité ; il prépare les variables, le `.gitignore` et le mécanisme de configuration.

---

## 1. Objectif et périmètre

Définir **l'état de production visé** avant de modifier tout mécanisme de sécurité, afin que chaque correctif (C1, C2, C3, E4…) s'insère dans une vision cohérente plutôt que d'être une rustine isolée.

Périmètre : configuration, secrets, desserte des fichiers, transport/sessions, journalisation, procédure de déploiement. Hébergement cible : **o2switch (Apache + Phusion Passenger)**, tel qu'utilisé aujourd'hui.

Hors périmètre (mentionnés pour cohérence, lots séparés) : base de données (E6), refonte fonctionnelle, qualité de code.

## 2. État actuel constaté (rappel factuel)

- **Deux environnements publics** pilotés par le module de settings : `config.settings` (prod principale, `psm2s.pbci-conseils.fr`) et `config.settings_formation` (`formation.…`), via `passenger_wsgi.py` et `passenger_wsgi_formation.py`.
- **`DEBUG = True` en dur** dans les deux modules (C1).
- **`SECRET_KEY`** lue depuis l'environnement mais **injectée en clair** dans les `passenger_wsgi*.py`, avec fallback `django-insecure-…` (C2).
- **Médias servis par Django** via `static(MEDIA_URL, …)` dans `config/urls.py`, **actif car `DEBUG=True`**, donc `/media/**` public et non authentifié (C3).
- **Transport** : `SECURE_PROXY_SSL_HEADER` est positionné (HTTPS derrière proxy o2switch), mais `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` sont absents (E4).
- **`ALLOWED_HOSTS`** correctement renseigné.
- **`.htaccess`** quasi vide (aucune règle de protection de `/media` ni de `db.sqlite3`).
- **Secrets et données dans l'arborescence de code** : `db.sqlite3`, `media/`, `logs/`, `*.bak` au même niveau que le code ; pas de `.gitignore` robuste constaté.

## 3. Principes directeurs de la cible

0. **Sécurité de déploiement pilotée par variables dédiées** (ajouté en E4, 03/07/2026) : *les comportements de sécurité dépendant de l'environnement de déploiement (HTTPS, HSTS, cookies sécurisés, etc.) sont pilotés par des variables d'environnement **dédiées** et ne doivent **jamais** être déduits indirectement de `DEBUG`.* Motif démontré : la suite de tests s'exécute en `DEBUG=False` ; dériver `SECURE_SSL_REDIRECT` de `not DEBUG` provoquerait des redirections 301 en test. Une variable explicite par comportement évite ces effets de bord.
1. **Secure-by-default** : la valeur sûre est celle obtenue « quand on ne fait rien ». Toute ouverture (DEBUG, desserte publique) est un acte explicite.
2. **Séparation configuration / code** : aucun secret ni réglage d'environnement en dur dans le code versionné.
3. **Séparation données / code** : base, médias, logs et secrets **hors de l'arborescence servie** et hors Git.
4. **Le serveur web sert les fichiers statiques ; Django protège les fichiers sensibles.**
5. **Barrière de déploiement** : un contrôle automatique empêche une mise en production non conforme.
6. **Minimalisme o2switch** : rester dans les capacités de l'hébergement mutualisé (Passenger, Apache, variables d'environnement d'application, cron), sans surcouche inutile.

## 4. Architecture cible par domaine

### 4.1 Configuration & secrets (couvre C1 et C2)

**Cible** : toutes les valeurs sensibles ou dépendantes de l'environnement proviennent de **variables d'environnement**, avec **défauts sûrs**, chargées depuis une source **hors code versionné**.

- Source des variables : soit les variables d'environnement de l'application Passenger (cPanel o2switch), soit un fichier `.env` **hors webroot** et **hors Git**, chargé au démarrage. (Décision §7.)
- `DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'` → **défaut False** (C1). La prod ne définit rien.
- `SECRET_KEY = os.environ['DJANGO_SECRET_KEY']` **sans fallback** : absence = échec explicite au démarrage plutôt que clé faible silencieuse (C2). Rotation de la clé actuelle (exposée) lors du lot C2.
- Les `passenger_wsgi*.py` ne contiennent **plus** de secret en clair : ils lisent l'environnement.
- `.gitignore` durci : `db.sqlite3`, `media/`, `logs/`, `.env`, `*.bak`, `__pycache__/`.

### 4.2 Séparation dev / prod

Deux options (décision §7) :
- **Option A (recommandée, minimale)** : un seul jeu de settings, tout le comportement dev/prod piloté par variables d'environnement (`DJANGO_DEBUG`, etc.). Léger, cohérent avec l'existant.
- **Option B** : `config/settings/{base,dev,prod}.py`, `DJANGO_SETTINGS_MODULE` fixant `prod` en production. Plus explicite, mais refactor plus large (tous les `wsgi`/`asgi`/`manage`/`passenger`).

Le cas `settings_formation` (sous-domaine public) est aligné sur le même principe : `DEBUG` par défaut False, opt-in explicite seulement si le DT le décide pour la formation.

### 4.3 Desserte des fichiers (couvre C3)

**Statique** (`/static/`) :
- `collectstatic` → `STATIC_ROOT` ; desserte par **Apache** (o2switch) directement, **pas** par Django. (Alternative : WhiteNoise, déjà dans `requirements.txt` mais non activé — décision §7.)
- Conséquence : la desserte via `static()` dans `urls.py` n'est plus nécessaire une fois `DEBUG=False`.

**Médias** (`/media/`) — cœur de C3 :
- Les fichiers médias sont **confidentiels** (PV, contrats, signatures). Cible : **aucune desserte publique directe**.
- Deux niveaux : (a) stockage **hors webroot** + blocage Apache de tout accès direct à `/media` ; (b) desserte via une **vue Django authentifiée** qui vérifie le périmètre (réutilise `verifier_acces_etablissement` / `_get_etab_ids_autorises`), idéalement avec délégation au serveur (`X-Sendfile` / `X-Accel-Redirect`) pour la performance.
- Renommage des fichiers avec identifiant non prédictible (défense en profondeur).
- **C3 réutilise donc directement l'acquis de la campagne C4** (la primitive de périmètre) — cohérence forte.

### 4.4 Transport & sessions (couvre E4)

Cible en production (`DEBUG=False`, HTTPS via proxy o2switch déjà signalé) :
- `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`.
- `SESSION_COOKIE_HTTPONLY = True` (défaut Django), `SESSION_COOKIE_SAMESITE = 'Lax'`.
- `SECURE_SSL_REDIRECT = True` (cohérent avec `SECURE_PROXY_SSL_HEADER` déjà présent).
- `SECURE_HSTS_SECONDS` progressif (ex. 3600 en rodage puis 31536000), `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` à activer prudemment.
- `CSRF_TRUSTED_ORIGINS` = domaines HTTPS déclarés.
- Tous ces réglages **pilotés par l'environnement** (activés en prod, désactivables en dev pour ne pas gêner le local en HTTP).

### 4.5 Journalisation & pages d'erreur

- `LOGGING` défini : erreurs applicatives vers un fichier de `logs/` (hors webroot) ; les échecs aujourd'hui « silencieux » (envois d'e-mails) y remontent.
- Pages `404.html` / `500.html` vérifiées pour un rendu propre en `DEBUG=False`.

### 4.6 Base de données (E6 — hors périmètre immédiat, cible à acter)

- SQLite dans l'arborescence de code est fragile (verrous, sauvegarde, déploiement). **Cible recommandée** : MySQL/MariaDB o2switch, ou a minima base **hors webroot** + mode WAL + sauvegardes. Décision distincte (lot E6), mais la cible de production doit la nommer pour cohérence.

### 4.7 Sauvegardes

- Sauvegardes planifiées et testées de : base de données, dossier `media/`, et le fichier de secrets — toutes hors dépôt Git.

### 4.8 Barrière de déploiement

- `python manage.py check --deploy` intégré à la procédure de mise en production, traité comme **bloquant**. Il couvre nativement plusieurs de nos points (DEBUG, cookies, HSTS…) et devient le garde-fou anti-régression de configuration.
- Checklist de déploiement documentée (collectstatic, migrations, variables d'environnement présentes, `check --deploy` vert).

## 5. Cartographie anomalies → architecture cible

| Anomalie | S'inscrit dans | Dépendances |
|---|---|---|
| **C1** DEBUG | §4.1 (env, défaut False) + §4.8 (gate) | **couplée à C3** (desserte fichiers) |
| **C2** SECRET_KEY | §4.1 (env sans fallback, rotation) | indépendante ; rapide |
| **C3** Médias | §4.3 (desserte protégée) | réutilise primitive C4 ; **couplée à C1** |
| **E4** Cookies/transport | §4.4 | s'active pleinement avec `DEBUG=False` (donc après/avec C1) |
| (E6 BD) | §4.6 | lot séparé |

**Constat structurant** : C1 et C3 forment un **couple** (couper DEBUG casse la desserte `static()` si la desserte statique/médias n'est pas refaite). E4 prend son sens une fois `DEBUG=False`. C2 est autonome.

## 6. Séquencement proposé des lots (à valider)

1. **Socle configuration** (petit lot préparatoire) : `.gitignore` durci, chargement des variables d'environnement, sortie des secrets du code — sans encore couper DEBUG. Prépare C1/C2.
2. **C2** (SECRET_KEY) : autonome, faible risque, fort gain — bon candidat pour être fait tôt.
3. **C3** (desserte médias protégée + statique par Apache) : la brique qui **débloque** le passage à `DEBUG=False`.
4. **C1** (DEBUG défaut False) + **E4** (cookies/HSTS) : déployés **ensemble**, une fois C3 en place, avec `check --deploy` comme gate.
5. (Ultérieur) **E6** base de données, puis reste de l'audit.

Cet ordre respecte les dépendances : rien ne casse la desserte des fichiers, et chaque lot reste « une anomalie = un lot », mais tous s'emboîtent dans la cible définie ici.

## 7. Décisions requises du Directeur Technique

1. **Injection des variables d'environnement sur o2switch** : variables d'application Passenger (cPanel) **ou** fichier `.env` hors webroot ? (impacte §4.1)
2. **Séparation dev/prod** : Option A (env-driven, minimal) **ou** Option B (split settings) ? (recommandation : A)
3. **Statique** : Apache direct (`collectstatic` + règles) **ou** activation de WhiteNoise (déjà en dépendances) ? (recommandation : Apache sur o2switch)
4. **Médias** : desserte par vue Django authentifiée avec délégation `X-Sendfile`/`X-Accel` **ou** vue Django simple (streaming Python) ? (recommandation : X-Sendfile si disponible o2switch, sinon vue simple)
5. **Environnement formation** : `DEBUG=False` aussi, ou opt-in `True` assumé et documenté ?
6. **Base de données** : acter la cible MySQL/MariaDB pour E6, ou rester SQLite hors webroot ?

## 8. Ce qui ne change pas

- Le code applicatif métier (vues, modèles, templates) n'est pas concerné par cette phase.
- `ALLOWED_HOSTS` est déjà correct.
- La primitive d'autorisation de la campagne C4 est **réutilisée** par C3 (pas de nouvelle logique d'accès à inventer).
- La suite de 90 tests reste la référence de non-régression ; elle sera complétée par des tests de configuration (parsing `DJANGO_DEBUG`, `check --deploy`) au fil des lots.

---

## Synthèse pour décision

Cette architecture pose une cible **secure-by-default** où configuration et secrets sortent du code, où le serveur web sert le statique et où Django protège les médias, et où une barrière `check --deploy` empêche toute régression de configuration. Les lots C1/C2/C3/E4 y deviennent des incréments cohérents, avec un **séquencement dicté par les dépendances** (C2 autonome ; C3 avant/ avec C1 ; E4 avec C1). J'attends tes arbitrages sur les six décisions du §7 avant d'ouvrir le premier lot préparatoire — toujours sans écrire de code tant que la cible n'est pas validée.
