# PSM2S — Procédure officielle de déploiement sur o2switch

> **Statut : document permanent et officiel de la plateforme** (validé DT, 02/07/2026),
> au même titre que l'Architecture de Production v1. Référence pour **toutes** les
> mises en production de PSM2S. Toute mise en production doit s'y conformer, ou
> justifier explicitement un écart en revue.

Document opérationnel, support de l'**Architecture de Production v1**.
Créé au lot **INFRA-1** (02/07/2026).

Principe : la configuration sensible ou dépendante de l'environnement est lue
depuis des **variables d'environnement** (Passenger / cPanel o2switch), jamais
codée en dur. Les défauts du code sont **sûrs** (secure-by-default).

---

## 1. Mécanisme

Les helpers `config/env.py` (`get_env`, `get_env_bool`) lisent l'environnement.
`config/settings.py` les utilise. Aujourd'hui (après INFRA-1), une seule
variable est câblée :

| Variable | Type | Défaut (code) | Effet |
|---|---|---|---|
| `DJANGO_DEBUG` | booléen | **`False`** | Active le mode debug Django si `True` |

Valeurs reconnues comme vraies : `true`, `1`, `yes`, `on` (insensible à la casse).
Toute autre valeur, ou l'absence de la variable, donne `False`.

## 2. Règle de transition (préparer ≠ activer) — procédure unique

Conformément à l'Architecture de Production v1 (secure-by-default), **la production
ne définit jamais `DJANGO_DEBUG`** : le défaut sûr `False` s'applique donc en
production. Il n'existe **qu'une seule procédure**, sans état intermédiaire
incohérent :

1. INFRA-1 est un lot de **préparation du dépôt**. Son code (défaut `False`) reste
   en dépôt et **n'est pas déployé seul** en production.
2. La production n'est mise à jour qu'au sein de la **release C1**, une fois **C3
   prêt** (desserte du statique par Apache + médias protégés). C'est à cet instant,
   et à cet instant seulement, que `DEBUG=False` prend effet en production — sans
   jamais passer par un état où la production afficherait des tracebacks ni où la
   desserte des fichiers serait cassée.
3. **Aucune variable `DJANGO_DEBUG=True` n'est jamais posée en production** : cela
   recréerait précisément l'état non sûr que C1 supprime.

En résumé : on **prépare** le mécanisme maintenant (INFRA-1), on **active**
`DEBUG=False` en production plus tard (release C1 + C3), en **une seule bascule
propre**, validée par `python manage.py check --deploy` (aucun `security.W018`).

## 3. Développement local

Après INFRA-1, en local, `DEBUG` vaut `False` par défaut. Pour retrouver le mode
debug en développement, définir la variable avant de lancer le serveur :

```
# Linux / macOS
export DJANGO_DEBUG=True
python manage.py runserver

# Windows PowerShell
$env:DJANGO_DEBUG = "True"
python manage.py runserver
```

Un fichier `.env` **local** peut porter cette variable ; il est ignoré par Git
(`.gitignore`) et **ne fait pas partie** de l'architecture de production.

## 3 bis. `DJANGO_SECRET_KEY` (lot C2) — variable **requise**

Depuis C2, `DJANGO_SECRET_KEY` est **obligatoire** dans tous les environnements
(dev, préproduction, production). Elle n'a **aucune valeur de secours** : si elle
est absente ou vide, l'application refuse de démarrer avec le message
`DJANGO_SECRET_KEY environment variable is required.` Aucun secret n'est plus
présent dans le code (`settings.py`, `passenger_wsgi*.py`).

**Développement local** — poser la variable avant toute commande Django :
```
# Windows PowerShell
$env:DJANGO_SECRET_KEY = "<clé de dev quelconque, non partagée>"
python manage.py test registre

# Linux / macOS
export DJANGO_SECRET_KEY="<clé de dev>"
```
(ou dans un `.env` local ignoré par Git). La clé de dev n'a pas besoin d'être la
clé de production.

**Générer une clé robuste** :
```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Procédure de rotation de la clé de production (responsabilité exploitant)

> Les clés présentes jusqu'ici dans le code sont **compromises** (versionnées / sauvegardées). Elles doivent être remplacées.

1. **Générer** une nouvelle clé (commande ci-dessus).
2. **Sauvegarder** la configuration actuelle (variables cPanel, `.htaccess`).
3. **Créer/mettre à jour** la variable `DJANGO_SECRET_KEY` dans cPanel (application Passenger) — pour la prod **et** pour la formation (clés distinctes).
4. **Vérifier** la présence de la variable (sans l'afficher dans des logs).
5. **Déployer** le code C2.
6. **Redémarrer** l'application Passenger.
7. **Contrôler** : la page de connexion s'affiche, connexion possible.

**Conséquence à anticiper** : la rotation **invalide les sessions actives** (déconnexion des utilisateurs) et les **liens de réinitialisation de mot de passe** en cours (signés avec l'ancienne clé). À réaliser de préférence hors heures de pointe, avec information des utilisateurs si nécessaire.

**Ordre impératif** : la variable `DJANGO_SECRET_KEY` doit exister dans cPanel **avant** le déploiement de C2 (sinon l'application ne démarre pas — comportement voulu, secure-by-default).

## 3 ter. Desserte des médias (lot C3-1)

Depuis C3-1, `/media` n'est **plus** servi par `static(MEDIA_URL, …)` mais par
la vue Django `media_protegee` (route `/media/<path>`), qui exige
l'authentification et applique le contrôle de périmètre pour les documents
métier. La politique par famille de fichiers est centralisée dans
`registre/media_access.py` (registre des préfixes).

**Apache / `.htaccess`** : ne **pas** ajouter de règle « Deny /media » (elle
renverrait 403 avant Django et casserait l'accès légitime). Le `.htaccess`
fournit un durcissement sûr (`Options -Indexes`).

**Protection définitive (Étape 2, ultérieure)** : déplacer `MEDIA_ROOT` **hors
du webroot** pour garantir qu'aucun fichier média n'est atteignable directement
par Apache. À planifier une fois la plateforme stabilisée. L'optimisation
`X-Sendfile` (délégation de l'envoi au serveur) relève également de cette Étape 2.

**Signatures** (lot **C3-2**, définitif) : signature **personnelle** → propriétaire
strict (aucune exception, même admin) ; signatures **DUERP** et **Accessibilité** →
périmètre de l'établissement du document. Tout préfixe média absent du registre
`media_access.py` est refusé (404).

## 3 quater. Mise en service `DEBUG=False` (lot C1)

**Principe** : la production **ne définit pas** `DJANGO_DEBUG` → le défaut sûr
`False` s'applique. `DEBUG=True` n'est jamais posé en production.

**Procédure d'activation** (ordre impératif) :
1. `DJANGO_SECRET_KEY` déjà présente (C2). `DJANGO_DEBUG` **absente** (ou `False`).
2. Déployer le code (git pull).
3. `python manage.py collectstatic --noinput` (statique servi par Apache).
4. `python manage.py migrate` (aucune migration attendue pour C1).
5. `python manage.py check --deploy` → **`security.W018` doit être ABSENT**
   (barrière C1). Les avertissements cookies/HSTS restants relèvent de **E4**.
6. Redémarrer l'application Passenger (`touch tmp/restart.txt` / cPanel).
7. Dérouler la **checklist post-déploiement** (§6).

**Plan de retour arrière (rollback)** — en cas de problème après bascule,
temporairement et brièvement, le temps du diagnostic :
1. Définir `DJANGO_DEBUG=True` dans cPanel (application Passenger).
2. Redémarrer Passenger → `DEBUG` repasse à `True` (état d'avant bascule ;
   la desserte média est inchangée car indépendante de `DEBUG` depuis C3).
3. Analyser (logs, reproduction en préproduction), corriger, retester.
4. **Retirer** `DJANGO_DEBUG` pour revenir à l'état sûr `False`.
⚠ Le rollback réexpose les tracebacks : il doit rester **exceptionnel et bref**,
jamais un état durable. Corriger la cause racine et revenir à `DEBUG=False` vite.

## 3 quinquies. Transport sécurisé (lot E4)

**Principe** (Architecture v1) : les comportements de sécurité liés au déploiement
sont pilotés par des variables **dédiées**, jamais dérivés de `DEBUG`.

| Variable | Type | Défaut | Effet en production |
|---|---|---|---|
| `DJANGO_SSL` | booléen | `False` | `True` → `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` activés |
| `DJANGO_HSTS_SECONDS` | entier | `0` | `max-age` HSTS (montée progressive) |
| `DJANGO_HSTS_INCLUDE_SUBDOMAINS` | booléen | `False` | `includeSubDomains` (à différer) |

Toujours actifs (code) : `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`,
`CSRF_COOKIE_SAMESITE='Lax'`. `SECURE_HSTS_PRELOAD=False` (jamais activé pour l'instant).

### Prérequis — vérification du proxy HTTPS (exploitation)
Avant d'activer `DJANGO_SSL=True`, **vérifier** que Django détecte bien le HTTPS
(sinon boucle de redirection) :
- Tester `request.is_secure()` en HTTPS. S'il est déjà `True` sans
  `SECURE_PROXY_SSL_HEADER`, envisager de **retirer** ce réglage (plus sûr).
- S'il est `False`, **conserver** `SECURE_PROXY_SSL_HEADER` et confirmer qu'Apache/o2switch
  **définit et écrase** `X-Forwarded-Proto` (le client ne peut pas l'usurper).

### Activation progressive HSTS (Option C, décision DT)
```
DJANGO_HSTS_SECONDS = 300        # étape 1 — validation prudente (5 min)
        ↓ (après vérification HTTPS irréprochable)
DJANGO_HSTS_SECONDS = 86400      # étape 2 — 1 jour
        ↓ (après stabilité confirmée)
DJANGO_HSTS_SECONDS = 31536000   # étape 3 — 1 an (valeur cible)
```
`includeSubDomains` : n'activer (`DJANGO_HSTS_INCLUDE_SUBDOMAINS=True`) **qu'après**
avoir confirmé le HTTPS des DEUX domaines (psm2s **et** formation), à un palier avancé.
`preload` : **NON** — engagement durable vis-à-vis des navigateurs (retrait en
plusieurs mois), envisagé seulement après plusieurs mois d'exploitation stable.

### Ordre d'activation (exploitation)
1. Vérifier la détection HTTPS (ci-dessus).
2. Poser `DJANGO_SSL=True` en cPanel → redémarrer Passenger → vérifier connexion
   et absence de boucle de redirection.
3. Poser `DJANGO_HSTS_SECONDS=300` → redémarrer → vérifier l'en-tête HSTS.
4. Monter par paliers (86400, puis 31536000) selon la stabilité.
5. `python manage.py check --deploy` → **entièrement vert** (W004/W008/W012/W016 levés).

### Rollback E4
- Cookies / redirection : `DJANGO_SSL=False` (ou retirer) + redémarrage Passenger → immédiat.
- HSTS : `DJANGO_HSTS_SECONDS=0` (sert `max-age=0`, efface HSTS pour les navigateurs
  qui reviennent en HTTPS) + redémarrage. ⚠ Un `max-age` **long** déjà mémorisé ne
  peut pas être « déprogrammé » à distance → c'est pourquoi la montée est progressive.

## 3 sexies. Fichiers spécifiques au serveur (jamais dans Git)

*(ajouté le 04/07/2026, suite à un incident réel lors de L3.1 — resynchronisation
de la plateforme formation)*

**Principe** : deux catégories de configuration cohabitent dans certains
fichiers, et ne doivent jamais être confondues.

- **Configuration de l'application** (portable, versionnée dans Git) :
  règles de sécurité génériques (`Options -Indexes`…), code Python.
- **Configuration de l'hébergement** (propre à CHAQUE serveur/domaine,
  jamais versionnée) : directives Passenger générées par cPanel/CloudLinux,
  chemins absolus (`PassengerAppRoot`, `PassengerPython`…), fichier
  `settings_formation.py` (ou équivalent par instance).

Écraser en aveugle un fichier de la seconde catégorie avec la version Git
casse l'environnement cible (incident vécu : `.htaccess` sans directives
Passenger → « No such application » ; `passenger_wsgi.py` de la production
copié sur formation → `DisallowedHost`).

**Étape de vérification — fichiers spécifiques au serveur**, à dérouler
avant tout déploiement (nouveau serveur ou mise à jour) :

- [ ] `.htaccess` : conserver le bloc Passenger existant du serveur cible
      (encadré `# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION
      BEGIN/END` sur o2switch/CloudLinux), fusionner **manuellement**
      uniquement les règles de sécurité portables en dessous. Ne jamais
      committer un `.htaccess` contenant des chemins serveur dans Git.
- [ ] `passenger_wsgi.py` : vérifier qu'il correspond bien à l'environnement
      cible (chemin `sys.path`, `DJANGO_SETTINGS_MODULE`). Ne jamais copier
      celui d'un autre environnement, même si le dépôt Git porte des noms
      distincts (`passenger_wsgi.py` / `passenger_wsgi_formation.py`) pour
      les versionner ensemble — sur le serveur, chaque environnement a son
      propre fichier, nommé localement `passenger_wsgi.py`.
- [ ] `config/settings_formation.py` (ou équivalent par instance) :
      conserver le fichier du serveur, ne jamais l'écraser depuis Git.
- [ ] Variables d'environnement : vérifier la présence de
      `DJANGO_SECRET_KEY` (obligatoire) et l'absence/présence voulue de
      `DJANGO_DEBUG` / `DJANGO_SSL` pour l'environnement cible.

Recommandation de fond : dès que possible, faire passer chaque plateforme
sous Git (`Git Version Control` cPanel) plutôt que par FTP manuel — un
déploiement par diff ciblé sur un commit de référence s'est révélé
insuffisant lorsque l'état réel du serveur ne correspond à aucun commit
connu (voir compte-rendu L3.1).

## 4. Variables (récapitulatif)

| Variable | Lot | Rôle |
|---|---|---|
| `DJANGO_DEBUG` | INFRA-1 / C1 | Mode debug (absent en prod → False) |
| `DJANGO_SECRET_KEY` | C2 | Clé secrète (requise, sans fallback) |
| `DJANGO_SSL` | E4 | Redirection HTTPS + cookies `Secure` |
| `DJANGO_HSTS_SECONDS` | E4 | HSTS `max-age` (progressif) |
| `DJANGO_HSTS_INCLUDE_SUBDOMAINS` | E4 | HSTS sous-domaines (différé) |
| `DJANGO_ALLOWED_HOSTS` | L3.4 | Domaine(s) de l'instance (défaut = domaine prod actuel) |
| `DJANGO_BASE_URL` | L3.4 | URL de base (emails), défaut = URL prod actuelle |
| `DJANGO_NOM_ORGANISATION` | L3.4 | Nom affiché dans le tableau de bord |
| `DJANGO_NOM_AFFICHE` | L3.4 | Nom affiché dans la sidebar (défaut `PSM2S`) |
| `DJANGO_SOUS_TITRE_LOGO` | L3.4 | Sous-titre du logo (défaut `Registre de sécurité`) |
| `DJANGO_COULEUR_ACCENT` | L3.4 | Couleur d'accent du thème (défaut `#185FA5`) |
| `DJANGO_COULEUR_SIDEBAR` | L3.4 | Couleur de fond de la sidebar (défaut `#0F2544`) |
| `DJANGO_EMAIL_HOST_USER` | L3.4 | Identifiant SMTP (défaut vide) |
| `DJANGO_EMAIL_HOST_PASSWORD` | L3.4 | Mot de passe SMTP (défaut vide) |
| `DJANGO_DEFAULT_FROM_EMAIL` | L3.4 | Adresse d'envoi des emails (défaut actuel) |
| `DJANGO_MODULES_ACTIFS` | L3.4 | Modules activés, liste séparée par virgules parmi `eau,commissions,duerp,accessibilite,tickets` (défaut : tous actifs — `tickets` non câblé dans le code à ce stade, voir `registre/permissions.py`) |

Toutes ces variables sont **optionnelles** : en leur absence, l'instance se
comporte exactement comme avant L3.4 (identité PSM2S/ADPEP28 actuelle, tous
les modules actifs). Voir `POLITIQUE-001` et
`Documentation/Developpements/2026-07-04_L3.4.4_Architecture_Core_Variantes.md`
pour le détail de l'architecture.

## 5. Procédure cible de mise en production (rappel, finalisée aux lots C1/C3)

0. Vérifier les **fichiers spécifiques au serveur** (§3 sexies) avant tout
   transfert — `.htaccess`, `passenger_wsgi.py`, `settings_formation.py`.
1. Définir les variables d'environnement de l'application (cPanel Passenger).
2. `python manage.py collectstatic` ; desserte du statique par Apache.
3. `python manage.py migrate`.
4. `python manage.py check --deploy` → **doit être vert** (bloquant).
5. Redémarrage de l'application Passenger.
6. Dérouler la **checklist de validation post-déploiement** (§6).

## 6. Checklist de validation post-déploiement

À dérouler **après chaque mise en production**. Les points marqués *(Cx)* ne
s'appliquent qu'une fois le lot correspondant déployé.

**Sécurité / configuration**
- [ ] `python manage.py check --deploy` : aucun avertissement (bloquant).
- [ ] Provoquer une URL en erreur → page 500 sobre, **aucun traceback** (`DEBUG=False` effectif). *(C1)*
- [ ] Aucun secret en clair dans le code déployé ; `DJANGO_SECRET_KEY` fournie par l'environnement. *(C2)*

**Fichiers**
- [ ] CSS / icônes / fichiers statiques chargés (`collectstatic` + Apache).
- [ ] Un fichier `/media/…` n'est **pas** accessible sans authentification. *(C3)*

**Fonctionnel**
- [ ] Connexion opérationnelle (`/connexion/`).
- [ ] Tableau de bord, calendrier et fiche établissement s'affichent correctement.
- [ ] Un utilisateur restreint ne voit que son périmètre (contrôle IDOR — non régressé).

**Transport / exploitation**
- [ ] HTTPS forcé ; cookies `Secure` et HSTS actifs. *(E4)*
- [ ] Journaux applicatifs écrits dans `logs/` (hors webroot).
- [ ] Sauvegardes base de données + dossier `media/` planifiées **et testées**.

En cas d'échec d'un point bloquant (check --deploy, traceback visible, média
public), **rollback immédiat** vers la version précédente et analyse avant
nouvelle tentative.
