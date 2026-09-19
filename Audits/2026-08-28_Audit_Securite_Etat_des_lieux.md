# Audit sécurité PSM2S — État des lieux (étape 1)

Date : 28/08/2026
Méthode : lecture seule du code source et de la configuration (`config/settings.py`, `config/settings_formation.py`, `requirements.txt`, `registre/permissions.py`, `registre/admin.py`, `config/urls.py`, `.gitignore`). Aucune modification, aucune migration, aucun redémarrage.
Limite assumée : aucun accès direct au serveur (SSH) ni au navigateur pendant cette étape (indisponibles techniquement au moment de l'audit) — tout ce qui nécessite une vérification en conditions réelles est marqué **INCONNU / NON ACCESSIBLE**, jamais déduit.

---

## 1. Hébergement / infrastructure

| Élément | Statut | Détail |
|---|---|---|
| Hébergeur | CONFIRMÉ | o2switch, France (cPanel, Passenger/mod_wsgi pour les apps Python) — connu par l'usage établi dans les échanges précédents, pas revérifié en direct aujourd'hui. |
| Serveur web / WSGI | CONFIRMÉ (code) | Passenger (`passenger_wsgi.py` à la racine de chaque instance). `gunicorn` est listé dans `requirements.txt` mais rien n'indique qu'il soit réellement utilisé en production — probablement une dépendance orpheline. |
| Version Python | INCONNU | Le dossier `virtualenv/.../3.9/` vu lors de manipulations précédentes suggère Python 3.9, mais non revérifié aujourd'hui. |
| Version Django | NON CONFIRMÉ | `requirements.txt` fixe seulement `django>=4.2`, **sans plafond de version** — impossible de savoir quelle version exacte tourne réellement sans lister les paquets installés sur le serveur (`pip freeze`). |
| Moteur base de données | CONFIRMÉ (code) | SQLite pour toutes les instances (`db.sqlite3` en production, `db_formation.sqlite3` en formation) — pas de PostgreSQL/MySQL. |
| HTTPS/TLS | NON CONFIRMÉ | Le code prévoit `SECURE_SSL_REDIRECT` piloté par la variable d'environnement `DJANGO_SSL` (défaut `False` si absente). Impossible de confirmer que cette variable est bien positionnée sur le serveur sans y accéder. |
| Configuration Apache/Nginx | INCONNU | Hors du dépôt de code, gérée côté cPanel. |
| Firewall / WAF | INCONNU | Rien dans le code applicatif ne l'indique ; relève de la configuration o2switch, non vérifiable ici. |
| Exposition des ports/services | INCONNU | Non vérifiable sans accès serveur ou scan réseau (non réalisé). |
| Accès SSH/SFTP/FTP | CONFIRMÉ (usage) | SSH utilisé (cPanel Terminal) et FileZilla (FTP/SFTP) — vu à l'usage dans les échanges précédents. Politique de mots de passe / clés non vérifiée. |
| Comptes admin connus | PARTIEL | Comptes applicatifs `demo_directeur`, `demo_factotum` (démo) connus. Comptes admin réels de production non recensés dans cet audit. |
| Sauvegardes | INCONNU | Des fichiers `.bak` et une archive `backup-formation-avant-lot2...zip` ont été aperçus dans un dossier via FileZilla lors d'une session précédente, ce qui suggère des sauvegardes **manuelles ponctuelles avant déploiement**, mais aucune preuve d'une politique de sauvegarde automatisée et régulière. |
| Procédure de restauration | NON CONFIRMÉ | Aucune procédure documentée trouvée dans `Documentation/08_Procedures/` à ce sujet (non revérifié en détail aujourd'hui). |
| Logs disponibles | PARTIEL | Un incident précédent a montré que `~/logs/` sur cPanel ne contient que les logs d'accès Apache, pas de trace applicative Python détaillée — confirmé par l'expérience directe (diagnostic DUERP du 24/08). |
| Surveillance / alertes | ABSENT | Aucun outil de monitoring/alerting trouvé dans le code ou mentionné dans la documentation du projet. |
| Politique de mise à jour (OS, dépendances) | ABSENT | Aucune procédure de mise à jour régulière des dépendances trouvée ; `requirements.txt` sans version plafonnée renforce le doute sur une politique formelle. |

## 2. Configuration Django de production (`config/settings.py`)

| Paramètre | Statut | Détail |
|---|---|---|
| `DEBUG` | 🟢 CONFIRMÉ sûr en production | Piloté par `DJANGO_DEBUG`, défaut `False`. **Mais `config/settings_formation.py` force `DEBUG = True` en dur, sans condition d'environnement** (voir section 5, finding critique). |
| `ALLOWED_HOSTS` | 🟢 CONFIRMÉ (code) | Liste explicite (`psm2s.pbci-conseils.fr`, etc.), pas de wildcard `*`. Valeur réellement active sur le serveur non revérifiée. |
| `SECRET_KEY` | 🟢 CONFIRMÉ bonne pratique | Lue exclusivement depuis l'environnement (`get_env_required`), **aucune valeur de secours en dur dans le code** — vérifié, aucune clé trouvée dans le dépôt local. `.env` et `Cle.txt` bien exclus du dépôt git (`.gitignore`). |
| CSRF | 🟢 CONFIRMÉ | `CsrfViewMiddleware` actif, `CSRF_COOKIE_SAMESITE = Lax`. `CSRF_COOKIE_SECURE` dépend de `DJANGO_SSL` (voir HTTPS ci-dessous). |
| Cookies de session | 🟢 CONFIRMÉ en partie | `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = Lax` toujours actifs. `SESSION_COOKIE_SECURE` dépend de `DJANGO_SSL` — non confirmé actif. |
| HTTPS forcé | 🟠 NON CONFIRMÉ | `SECURE_SSL_REDIRECT` = valeur de `DJANGO_SSL`, défaut `False`. Sans accès serveur, impossible de confirmer que cette variable est posée. |
| HSTS | 🟠 PROBABLEMENT INACTIF | `SECURE_HSTS_SECONDS` défaut `0` (désactivé), montée progressive prévue mais non confirmée activée à ce jour (dernière trace documentée : "montée progressive, décision DT" sans date de mise en service confirmée). |
| `X_FRAME_OPTIONS` | 🟢 CONFIRMÉ | `'DENY'`, protection anti-clickjacking active. |
| `SECURE_CONTENT_TYPE_NOSNIFF` | 🟢 CONFIRMÉ | `True`. |
| `SECURE_REFERRER_POLICY` | 🟢 CONFIRMÉ | `"same-origin"`. |
| Gestion des fichiers uploadés | 🟢 PARTIEL | `DATA_UPLOAD_MAX_MEMORY_SIZE = 20 Mo`. Aucune validation de type de fichier (extension/MIME) trouvée au niveau des formulaires d'upload (`Document`, `PieceJointeTicket`, signatures) — à vérifier plus précisément si nécessaire. |
| Médias/statiques | 🟢 CONFIRMÉ | Médias servis via une vue dédiée (`media_protegee`, mentionnée dans le code) plutôt que servis en statique brut — bonne pratique pour contrôler l'accès aux pièces jointes. Non re-testé en direct. |
| CORS | ABSENT (normal) | Aucun package CORS installé, aucune API cross-origin exposée — cohérent avec l'absence d'API. |
| Gestion des erreurs | 🟢 CONFIRMÉ en prod (sous réserve) | `DEBUG=False` par défaut en prod → pages d'erreur génériques Django. Pas de `ADMINS`/`SERVER_EMAIL` configurés pour recevoir une alerte par email en cas d'erreur 500 — absence à noter. |
| Exposition d'informations sensibles | 🔴 voir finding formation ci-dessous | |

## 3. Dépendances (`requirements.txt`)

```
django>=4.2
pillow
gunicorn
whitenoise
```

Aucune version plafonnée pour aucun paquet. Impossible de dire quelles versions exactes tournent réellement sans un `pip freeze` sur le serveur. Aucun paquet de sécurité applicative (pas de limitation de tentatives de connexion type `django-axes`, pas de `django-otp` pour une double authentification).

## 4. Sécurité applicative déjà développée

C'est le point le plus solide de l'audit.

- **`_get_etab_ids_autorises` / `verifier_acces_etablissement` / `get_etablissement_ou_404` / `get_prestataire_ou_404`** (`registre/permissions.py`) : mécanisme anti-IDOR centralisé, une seule source de vérité, réutilisé de façon cohérente. Retourne systématiquement `Http404` (jamais `403`) en cas d'accès hors périmètre — bonne pratique pour ne pas confirmer l'existence d'un objet à un utilisateur non autorisé. Historique du projet montre que ce mécanisme a déjà fait l'objet d'un audit dédié (Phase 1, C4-1 à C4-7) et d'au moins un correctif isolé découvert après coup (`registre_pdf`, 04/07/2026) — signe d'un processus de sécurité qui s'améliore dans la durée, pas d'un audit ponctuel figé.
- **`gestionnaire_requis` et la famille de décorateurs de rôle** (`acces_requis`, `admin_requis`, `operateur_requis`, `factotum_niveau_requis`, `module_requis`) : contrôle d'accès cohérent au niveau vue, avec une hiérarchie claire des rôles.
- **Authentification** : système Django standard (`AbstractUser` étendu), validateurs de mot de passe actifs (longueur mini, similarité, mots de passe courants, pas 100% numérique). Pas de double authentification (2FA) — absent.
- **Séparation des périmètres entre établissements** : confirmée par la conception (`etablissements_autorises` renvoie soit un accès total soit un ensemble d'IDs explicite), et par l'usage réel observé pendant les tests de ce projet (le compte `demo_directeur` ne voit que son établissement).
- **Administration Django** : accessible à l'URL par défaut `/admin/` (non renommée). Django restreint nativement l'accès aux comptes `is_staff`/`is_superuser`, indépendamment du champ métier `role` — cohérent, mais je n'ai pas vérifié combien de comptes ont `is_staff=True` en production.
- **API** : absente (pas de Django REST Framework ni d'app `api` dans `INSTALLED_APPS`) — surface d'attaque réduite d'autant.
- **Journalisation des actions sensibles** : partielle. De nombreux modèles ont `mis_a_jour_par` + `date_mise_a_jour`/`date_creation` (traçabilité de qui a modifié quoi), mais **aucun journal d'audit dédié** (pas de modèle de type "log d'activité" centralisé, pas de `LOGGING` Django personnalisé trouvé dans `settings.py`).

---

## 5. Rapport final

### 🔴 PROBLÈME IDENTIFIÉ

**`DEBUG = True` en dur sur l'instance formation**
- Risque : si une exception non gérée survient sur `formation.psm2s.pbci-conseils.fr`, Django peut afficher une page de traceback détaillée — potentiellement des extraits de code, des noms de variables, voire des valeurs de configuration selon le point de plantage.
- Preuve : `config/settings_formation.py` ligne 26, `DEBUG = True`, assignation en dur après l'import de `settings.py` (qui avait pourtant `DEBUG=False` par défaut) — aucune condition d'environnement.
- Emplacement : `config/settings_formation.py`.
- Gravité estimée : **élevée** (formation est un sous-domaine public, atteint par de vrais visiteurs potentiels, pas un environnement strictement privé). Nuance : lors d'un incident réel le mois dernier, le navigateur a affiché une erreur 500 générique, pas une page de debug Django — ce qui suggère qu'un mécanisme (probablement côté Apache/cPanel) intercepte les erreurs 500 avant que Django ne les affiche. Cela n'annule pas le risque : c'est une protection accidentelle, pas une configuration voulue, et elle pourrait ne pas couvrir tous les cas (erreurs 4xx, certains types d'exceptions).
- Recommandation : passer `DEBUG` en formation sur le même mécanisme piloté par variable d'environnement que la production (`DJANGO_DEBUG`), avec un défaut sûr `False`, plutôt qu'une valeur figée dans le code.

### 🟠 À VÉRIFIER

- **`DJANGO_SSL` réellement actif en production ?** Si cette variable d'environnement n'est pas positionnée sur le serveur, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` et `CSRF_COOKIE_SECURE` restent à `False` — cookies transmis sans le flag `Secure`, redirection HTTPS non forcée au niveau Django (même si o2switch fournit HTTPS par ailleurs, la protection applicative resterait désactivée). Gravité si absent : élevée. Vérification simple à faire depuis le serveur (`echo $DJANGO_SSL` dans l'environnement Passenger, ou via le fichier de configuration cPanel Python App).
- **`DJANGO_HSTS_SECONDS`** : probablement toujours à 0 (désactivé) d'après la dernière trace documentée du projet — à confirmer, gravité faible à moyenne (HSTS est un renforcement, pas une protection de base).
- **Version exacte de Django/Python réellement installée** — `requirements.txt` ne plafonne rien, seul un `pip freeze` sur le serveur donnerait la réponse exacte. Gravité potentielle moyenne si une version ancienne avec CVE connue tourne sans qu'on le sache.
- **Fichier `Cle.txt` visible à la racine de l'application** (aperçu lors d'un transfert FileZilla précédent) — à vérifier qu'il n'est pas directement accessible par une URL directe (`https://.../Cle.txt`). S'il ne contient pas de secret réel c'est sans gravité ; s'il en contient un, gravité critique. Vérification en 30 secondes : essayer l'URL directement, et si un secret y est stocké, le déplacer hors du dossier servi par l'application.
- **Politique de sauvegarde** : seules des sauvegardes manuelles ponctuelles avant déploiement ont été constatées, pas de preuve d'automatisation régulière — à confirmer directement avec l'hébergeur/cPanel (cPanel propose souvent un outil de sauvegarde automatique intégré, à vérifier s'il est activé).
- **`is_staff` sur les comptes de production** : combien de comptes ont accès à `/admin/` ? Pas vérifié dans cet audit.

### ⚪ INCONNU / NON ACCESSIBLE

Firewall/WAF, exposition réseau des ports, configuration Apache/Nginx détaillée, monitoring/alerting, politique de mise à jour système — tous nécessitent soit un accès SSH direct (indisponible pour moi aujourd'hui, technique et momentané), soit une vérification que seul toi peux faire côté hébergeur.

### 🟢 SÉCURISÉ / CONFIRMÉ

`SECRET_KEY` sans valeur de secours, aucun secret trouvé dans le dépôt git, mécanisme anti-IDOR centralisé et cohérent (`_get_etab_ids_autorises` et la famille de fonctions associées), séparation des rôles par décorateurs, `X_FRAME_OPTIONS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`, cookies `HttpOnly`/`SameSite=Lax` (indépendamment du flag `Secure`), pas d'API exposée, pas de CORS ouvert, validateurs de mot de passe actifs.

---

## Ce qu'il faudrait pour compléter cet audit

Une deuxième étape, avec accès SSH (donc avec toi, pas en autonomie), permettrait de lever la plupart des ⚪ et 🟠 : `pip freeze` pour les versions exactes, vérification des variables d'environnement `DJANGO_SSL`/`DJANGO_HSTS_SECONDS`, test direct de l'URL `Cle.txt`, vérification de la politique de sauvegarde cPanel, comptage des comptes `is_staff`. Je peux préparer un script de vérification en lecture seule pour cette étape, comme pour les audits de données précédents — dis-moi quand tu veux qu'on le fasse.

Aucune correction n'a été appliquée. En attente de ta lecture avant toute décision.
