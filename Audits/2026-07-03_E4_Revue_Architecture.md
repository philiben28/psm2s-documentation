# Revue d'architecture — Lot E4 : durcissement du transport (cookies, HTTPS, HSTS)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 03/07/2026
Nature : **revue / plan uniquement** (aucun code). Dernier lot de la Phase 2.

---

## 0. État actuel constaté (`config/settings.py`)

Déjà présents : `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`,
`SECURE_CONTENT_TYPE_NOSNIFF = True`, `X_FRAME_OPTIONS = 'DENY'`,
`SECURE_REFERRER_POLICY = 'same-origin'`, `SecurityMiddleware` en tête de `MIDDLEWARE`.
**Absents** : `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`,
tous les réglages HSTS. Ce sont les 4 avertissements de `check --deploy`
(W012, W016, W008, W004).

## ⚠ Constat technique majeur (préalable à tous les arbitrages)

**`SECURE_SSL_REDIRECT=True` casse la suite de tests si elle est active pendant les tests.**
La suite s'exécute nativement avec `DEBUG=False`. Le `SecurityMiddleware`, si
`SECURE_SSL_REDIRECT=True` et la requête non sécurisée (client de test en HTTP),
renvoie un **301 vers HTTPS** — nos 111 tests attendent 200/302/404 → ils
échoueraient en masse.

**Conséquence de conception** : les réglages de transport **ne doivent pas** être
dérivés de `not DEBUG` (car en test `DEBUG=False`). Ils doivent être pilotés par
une **variable d'environnement dédiée, défaut `False`**, que **seule la production
définit**. Ainsi : tests et dev inchangés (flag absent → False) ; production
sécurisée (flag présent → True). C'est aussi cohérent avec l'Architecture v1
(pilotage par l'environnement).

Proposition : un booléen `DJANGO_SSL` (défaut `False`) pour cookies + redirection,
et une variable numérique `DJANGO_HSTS_SECONDS` (défaut `0`) pour HSTS (progressif).

---

## 1. Cookies

| Paramètre | Valeur proposée | Effet | Risque | Justification |
|---|---|---|---|---|
| `SESSION_COOKIE_SECURE` | `DJANGO_SSL` (True en prod) | Cookie de session envoyé **uniquement en HTTPS** | Si HTTPS mal détecté → cookie non émis → déconnexions | Empêche le vol de session par écoute réseau (W012) |
| `CSRF_COOKIE_SECURE` | `DJANGO_SSL` (True en prod) | Cookie CSRF **HTTPS uniquement** | idem | Protège le jeton CSRF (W016) |
| `SESSION_COOKIE_HTTPONLY` | `True` (explicite ; = défaut Django) | JS ne peut pas lire le cookie de session | Aucun | Réduit le vol de session via XSS |
| `CSRF_COOKIE_HTTPONLY` | **`False` (défaut, laissé tel quel)** | — | Le passer à True peut gêner un AJAX qui lit le cookie | PSM2S place le jeton dans le formulaire (`{% csrf_token %}`), pas via JS ; Django lui-même recommande de ne pas s'appuyer dessus. Non requis par `check --deploy`. |
| `SESSION_COOKIE_SAMESITE` | `'Lax'` (explicite ; = défaut) | Cookie non envoyé sur requêtes cross-site (sauf navigation top-level) | `'Strict'` casserait l'arrivée via liens externes | `'Lax'` = bon équilibre CSRF / ergonomie |
| `CSRF_COOKIE_SAMESITE` | `'Lax'` (explicite ; = défaut) | idem | idem | idem |

Cookies `Secure` : **activables**, mais leur effet dépend de la bonne détection HTTPS (§2). HttpOnly/SameSite : **activables immédiatement** (défauts sûrs, sans risque, sans impact test).

## 2. HTTPS

- **`SECURE_SSL_REDIRECT`** : proposé à `DJANGO_SSL` (True en prod). Redirige HTTP→HTTPS au niveau Django. **Risque principal : boucle de redirection** si Django ne détecte pas correctement le HTTPS (il croit la requête en HTTP, redirige vers HTTPS, qui lui revient « HTTP », etc.). → à valider avec §2 bis avant activation. Alternative : laisser Apache/o2switch forcer HTTPS (souvent possible au niveau vhost/.htaccess) ; mais `check --deploy` (W008) attend `SECURE_SSL_REDIRECT=True`, donc on le met côté Django **une fois la détection validée**.

### 2 bis. `SECURE_PROXY_SSL_HEADER` — o2switch en a-t-il besoin ? (analyse, pas habitude)

Le réglage est **déjà présent** : `('HTTP_X_FORWARDED_PROTO', 'https')`. Il indique à Django de considérer la requête comme sécurisée si l'en-tête `X-Forwarded-Proto: https` est présent.

- **Nécessaire uniquement si** o2switch/Passenger ne renseigne pas nativement `HTTPS=on` dans l'environnement WSGI, mais transmet `X-Forwarded-Proto`.
- **Risque si mal utilisé** : si le proxy ne définit/écrase pas cet en-tête, un client pourrait l'usurper (`X-Forwarded-Proto: https`) et tromper Django.

**Recommandation** : ne pas trancher « par habitude ». **Vérifier** sur la production :
1. Tester `request.is_secure()` (ou un simple log) **sans** `SECURE_PROXY_SSL_HEADER`. S'il renvoie déjà `True` en HTTPS → Passenger fournit `HTTPS=on` → **retirer** `SECURE_PROXY_SSL_HEADER` (plus sûr, une dépendance de moins).
2. S'il renvoie `False` → **conserver** `SECURE_PROXY_SSL_HEADER`, après avoir confirmé que la couche Apache/o2switch **définit et écrase** `X-Forwarded-Proto` (le client ne peut pas l'usurper).

Cette vérification est **le prérequis** à l'activation de `SECURE_SSL_REDIRECT` et des cookies `Secure` (sinon boucle de redirection / cookies non émis).

## 3. HSTS — comparaison des stratégies

HSTS (`Strict-Transport-Security`) dit au navigateur : « pour ce domaine, n'utilise **que** HTTPS pendant `max-age` secondes ». **Effet persistant** : le navigateur mémorise l'instruction ; si le HTTPS casse (certificat expiré, mauvaise config), les visiteurs sont **bloqués** (impossible de rétrograder en HTTP) pour toute la durée.

| Option | Valeur | Analyse |
|---|---|---|
| **A** | `300` (5 min) | Sûr pour valider, mais trop court pour une vraie protection durable. Utile en **1re étape**. |
| **B** | `31536000` (1 an) | Protection définitive, mais **risquée d'emblée** : en cas de souci HTTPS, blocage jusqu'à 1 an côté navigateurs déjà venus. |
| **C** | Montée progressive `300 → 86400 → 31536000` | Valide à chaque palier avec un `max-age` court (rollback facile), puis augmente une fois la confiance acquise. |

**Recommandation : Option C.** C'est la seule qui combine protection cible et réversibilité pratique pendant la phase de validation. Chaque palier n'est franchi qu'après vérification que le HTTPS est irréprochable (certificat, renouvellement automatique, pas de contenu mixte). Piloté par `DJANGO_HSTS_SECONDS` (défaut `0` = HSTS désactivé en dev/test).

## 4. `SECURE_HSTS_INCLUDE_SUBDOMAINS`

Étend HSTS à **tous les sous-domaines**. Or `formation.psm2s.pbci-conseils.fr` est un sous-domaine de `psm2s.pbci-conseils.fr`. Activer `includeSubDomains` sur le domaine principal **forcerait HTTPS sur formation aussi**.

**Recommandation : PAS immédiatement.** À n'activer qu'après avoir **confirmé que les DEUX domaines** (psm2s **et** formation) ont un HTTPS solide (certificats valides, renouvellement automatique), et de préférence à un **palier avancé** de la montée HSTS (§3). Tant que l'un des deux n'est pas garanti, `includeSubDomains` peut bloquer un sous-domaine. → **« à valider », activation différée**, pilotée par une variable dédiée (défaut `False`).

## 5. `SECURE_HSTS_PRELOAD` — démonstration

`preload` ajoute la directive permettant d'inscrire le domaine dans les **listes de préchargement codées en dur dans les navigateurs**.

**Démonstration de l'irréversibilité** : une fois un domaine soumis et accepté dans ces listes, il est **codé dans les binaires des navigateurs** ; l'en retirer prend **des mois** (nouvelle version de navigateur diffusée), et pendant ce temps le HTTPS est **imposé sans recours**. C'est une **porte à sens unique**. Les prérequis officiels sont d'ailleurs stricts : `max-age ≥ 31536000` **et** `includeSubDomains` **et** `preload`, plus une soumission volontaire.

**Recommandation : NON, pas maintenant.** À ne considérer que **très tardivement**, après HSTS stable à 1 an + `includeSubDomains` validé sur la durée, et comme **décision délibérée** distincte. → `SECURE_HSTS_PRELOAD = False`.

## 6. Plan de rollback

Tous les réglages E4 étant **pilotés par l'environnement**, le retour arrière est immédiat, sans redéploiement de code :

**Cookies `Secure` / redirection SSL** :
1. Mettre `DJANGO_SSL=False` (ou retirer la variable) en cPanel.
2. Redémarrer Passenger. → cookies non-Secure, plus de redirection forcée.

**HSTS** (le point sensible) :
1. Mettre `DJANGO_HSTS_SECONDS=0` → l'application sert alors `max-age=0`, qui **efface** HSTS pour les navigateurs qui **reviennent en HTTPS** et reçoivent cet en-tête.
2. Redémarrer Passenger.
⚠ Limite intrinsèque : un navigateur ayant mémorisé un `max-age` **long** et qui **ne revient pas** ne peut pas être « déprogrammé » à distance. **C'est précisément pourquoi la montée est progressive** (§3) : tant que `max-age` est court, le rollback est réel et rapide.

**`SECURE_PROXY_SSL_HEADER`** : si une boucle de redirection apparaît, retirer `SECURE_SSL_REDIRECT` (via `DJANGO_SSL=False`) et diagnostiquer la détection HTTPS (§2 bis) avant de réactiver.

## 7. Validation — avertissements `check --deploy`

Après E4 **déployé en production** (avec `DJANGO_SSL=True` et `DJANGO_HSTS_SECONDS>0`) :

| Avertissement | Levé par | Statut |
|---|---|---|
| **W012** `SESSION_COOKIE_SECURE` | `SESSION_COOKIE_SECURE=True` | disparaît |
| **W016** `CSRF_COOKIE_SECURE` | `CSRF_COOKIE_SECURE=True` | disparaît |
| **W008** `SECURE_SSL_REDIRECT` | `SECURE_SSL_REDIRECT=True` | disparaît |
| **W004** HSTS | `SECURE_HSTS_SECONDS>0` | disparaît (dès le 1er palier) |
| **W009** `SECRET_KEY` | clé forte (rotation C2) | disparaît **en production** (clé locale courte = artefact dev) |

→ `check --deploy` **entièrement vert** en production une fois E4 activé et la clé de prod en place. **Clôture de la Phase 2.**

Note : en local (flag `DJANGO_SSL` absent, HSTS=0, clé de dev courte), `check --deploy` continuera d'afficher ces avertissements — c'est **normal et voulu** (les réglages de transport ne s'activent qu'en production). La preuve de vert se fait **en conditions de production** (ou en préproduction avec les variables posées).

---

## Synthèse des arbitrages proposés (à valider)

| Réglage | Proposition | Activation |
|---|---|---|
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | `DJANGO_SSL` (True en prod) | **immédiate** (après validation §2 bis) |
| `SESSION_COOKIE_HTTPONLY` | `True` | immédiate |
| `SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE` | `'Lax'` | immédiate |
| `CSRF_COOKIE_HTTPONLY` | `False` (défaut) | n/a |
| `SECURE_SSL_REDIRECT` | `DJANGO_SSL` | après validation détection HTTPS |
| `SECURE_PROXY_SSL_HEADER` | à **vérifier** (garder ou retirer) | selon test prod |
| `SECURE_HSTS_SECONDS` | `DJANGO_HSTS_SECONDS`, montée **300 → 86400 → 31536000** | **progressive** |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` d'abord | différée (après validation des 2 domaines) |
| `SECURE_HSTS_PRELOAD` | `False` | **non** (porte à sens unique) |

Cela correspond à ton intuition — Secure oui, HttpOnly oui, SameSite=Lax oui, HTTPS redirect oui, HSTS progressif, includeSubDomains à valider, preload non — avec en plus **deux points techniques** que la revue met en avant :
1. **Les réglages doivent être pilotés par une variable dédiée (`DJANGO_SSL`), défaut `False`** — pas dérivés de `not DEBUG` — sinon `SECURE_SSL_REDIRECT` **casserait la suite de tests**.
2. **`SECURE_PROXY_SSL_HEADER` doit être vérifié** (o2switch le nécessite-t-il vraiment ?) avant d'activer la redirection, pour éviter toute boucle.

## Décisions attendues du DT

1. Valides-tu le pilotage par **`DJANGO_SSL` (booléen, défaut False)** + **`DJANGO_HSTS_SECONDS` (numérique, défaut 0)**, plutôt qu'un couplage à `not DEBUG` (qui casserait les tests) ?
2. HSTS : confirmes-tu l'**Option C** (montée progressive) ?
3. `includeSubDomains` **différé** et `preload` **non** — d'accord ?
4. Acceptes-tu que l'activation effective (valeurs des variables en prod) et la **vérification `SECURE_PROXY_SSL_HEADER`** soient des **actions d'exploitation** (comme la rotation de clé), le développement se limitant à câbler proprement les réglages sur les variables d'environnement ?
