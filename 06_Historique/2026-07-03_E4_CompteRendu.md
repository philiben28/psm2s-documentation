# Compte-rendu de développement — Lot E4 : durcissement du transport

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 03/07/2026
Nature : correction de sécurité (E4). **Dernier lot de la Phase 2** (côté code).

---

## 1. Résumé

Câblage des réglages de transport (cookies `Secure`, HTTPS, HSTS), **pilotés par des variables d'environnement dédiées** — jamais dérivés de `DEBUG` (nouveau principe d'architecture v1). Défauts sûrs pour dev/tests : sans les variables, aucun changement de comportement, aucune régression.

## 2. Fichiers modifiés

| Fichier | Nature |
|---|---|
| `config/env.py` | **Ajout** `get_env_int(name, default=0)`. |
| `config/settings.py` | Bloc « TRANSPORT SÉCURISÉ (E4) » : `DJANGO_SSL` → SSL redirect + cookies `Secure` ; `DJANGO_HSTS_SECONDS` → HSTS ; HttpOnly/SameSite toujours actifs ; `preload=False`. |
| `registre/tests.py` | **3 tests** `get_env_int`. |
| `Documentation/Audits/2026-07-02_Phase2_Architecture_Production.md` | **Principe n°0** ajouté (v1). |
| `Documentation/DEPLOIEMENT_o2switch.md` | Section transport E4 : variables, vérif proxy, HSTS progressif, rollback, ordre d'activation. |
| `CHANGELOG.md` | Entrée E4. |

Sauvegarde : `Sauvegardes/2026-07-03_avant_E4/`. **Aucun modèle, migration, template.**

## 3. Réglages (rappel des décisions DT appliquées)

| Réglage | Câblage | Activation |
|---|---|---|
| `SECURE_SSL_REDIRECT` | `DJANGO_SSL` (défaut False) | prod, après vérif proxy |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | `DJANGO_SSL` | prod |
| `SESSION_COOKIE_HTTPONLY` | `True` (toujours) | immédiate |
| `SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE` | `'Lax'` (toujours) | immédiate |
| `CSRF_COOKIE_HTTPONLY` | défaut Django (`False`) | n/a |
| `SECURE_HSTS_SECONDS` | `DJANGO_HSTS_SECONDS` (défaut 0) | progressive `300→86400→31536000` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `DJANGO_HSTS_INCLUDE_SUBDOMAINS` (défaut False) | différée (2 domaines) |
| `SECURE_HSTS_PRELOAD` | `False` (en dur) | **non** (engagement durable) |

## 4. Non-régression garantie par conception

Les variables `DJANGO_SSL` / `DJANGO_HSTS_SECONDS` étant **absentes** en dev et en test :
- `SECURE_SSL_REDIRECT=False` → **pas de 301** en test (le point critique identifié en revue) ;
- cookies `Secure=False` → login local en HTTP possible ;
- HSTS désactivé.
→ Les **111 tests** existants ne sont pas affectés ; 3 tests `get_env_int` s'ajoutent.

## 5. Tests

> Pré-requis : `DJANGO_SECRET_KEY` posée.

**A. Non-régression (variables de transport absentes)** :
```
python manage.py test registre     # attendu : 114 tests OK (111 + 3)
```

**B. Preuve du câblage (variables posées, conditions de production)** :
```
$env:DJANGO_SSL="True"; $env:DJANGO_HSTS_SECONDS="300"
python manage.py check --deploy
```
**Résultat réel (03/07/2026) :** les 4 avertissements ciblés **W008, W012, W016,
W004** ont **disparu** → câblage validé. Trois avertissements demeurent, **tous
attendus** :

| Avert. | Sujet | Interprétation |
|---|---|---|
| **W005** | `SECURE_HSTS_INCLUDE_SUBDOMAINS` non activé | **Décision DT** : includeSubDomains **différé** (à activer après validation HTTPS de psm2s ET formation). Se lèvera à ce moment-là. |
| **W021** | `SECURE_HSTS_PRELOAD` non activé | **Décision DT** : preload **décliné** (engagement durable irréversible). **Résidu volontaire et permanent.** |
| **W009** | `SECRET_KEY` faible | Artefact clé de **dev** courte ; disparaît en production (clé forte, C2). |

**Précision (correction d'une formulation antérieure) :** `check --deploy` n'est
pas censé être « entièrement vert » tant que `preload` reste désactivé — W021 est
un avertissement **assumé par choix**. L'état cible de production est donc :
W004/W005/W008/W012/W016 levés (W005 une fois includeSubDomains activé), W009 levé
(clé de prod), et **W021 conservé volontairement**.

Penser à retirer ces variables ensuite (`Remove-Item Env:DJANGO_SSL, Env:DJANGO_HSTS_SECONDS`)
pour le travail local en HTTP.

## 6. Actions d'exploitation (hors développement)

- Vérification du proxy HTTPS (`request.is_secure()`), décision sur `SECURE_PROXY_SSL_HEADER`.
- `DJANGO_SSL=True` en cPanel, redémarrage Passenger.
- Montée progressive `DJANGO_HSTS_SECONDS`.
- `check --deploy` final vert.

## 7. Bilan Phase 2

Après E4 (code) : toute la sécurité applicative **et** de production est en place. Une fois E4 activé en production (variables posées) et la clé de prod en service, `check --deploy` ne conservera que **W021 (preload)** — **avertissement volontairement assumé** (decision DT), et éventuellement W005 tant qu'includeSubDomains n'est pas activé. Les 4 cibles historiques (W004/W008/W012/W016) et W009 sont levées. **Phase 2 close côté développement.**

Restent uniquement des **actions d'exploitation** (rotation clé, `DJANGO_SSL`, HSTS progressif, `collectstatic`, redémarrage) et, plus tard, l'**Étape 2** (MEDIA_ROOT hors webroot + X-Sendfile).

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : `DJANGO_SECRET_KEY` posée, `python manage.py check` et `python manage.py test registre` (attendu : **114 OK**), puis, en option, la preuve B ci-dessus. Me transmettre la sortie. Aucun commit effectué.
