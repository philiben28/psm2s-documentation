# PSM2S — Point de reprise (document de travail)

Dernière mise à jour : 03/07/2026.

## État du projet

- ✅ **Phase 1 — Sécurité applicative : CLÔTURÉE.**
  IDOR (C4-1 → C4-7, 54 vues), F9 (filtrage formulaires), E5 (visibilité DUERP),
  M11 (compat Python), BUG-TPL-01 (template).
- ✅ **Phase 2 — Sécurité de production : CLÔTURÉE (côté code).**
  INFRA-1, C2 (SECRET_KEY), C3-1 & C3-2 (médias protégés), C1 (DEBUG=False), E4 (transport).
- ✅ **114 tests automatisés au vert** ; `manage.py check` sans anomalie.
- ✅ **Architecture de Production v1 validée** (document de référence permanent) +
  **Procédure de déploiement o2switch** (document officiel).
- ✅ **Historique Git propre** : un commit par lot, poussé sur GitHub.

## ⏳ Actions d'EXPLOITATION restant à réaliser (hors développement)

À exécuter côté serveur, sous responsabilité de l'exploitant, selon
`Documentation/DEPLOIEMENT_o2switch.md` :

1. **Rotation des clés** `SECRET_KEY` (prod + formation, **deux clés distinctes**), posées en variables cPanel.
2. **Vérification du proxy HTTPS** (`request.is_secure()`) → décision sur `SECURE_PROXY_SSL_HEADER`.
3. **Activation `DJANGO_SSL=True`** (cookies Secure + redirection HTTPS).
4. **Montée progressive HSTS** `DJANGO_HSTS_SECONDS` : `300 → 86400 → 31536000` ;
   `includeSubDomains` différé (après validation HTTPS des 2 domaines) ; `preload` = non.
5. **Mise en service `DEBUG=False`** (ne pas définir `DJANGO_DEBUG` en prod).
6. `collectstatic`, `check --deploy`, redémarrage Passenger.

Rappel `check --deploy` après activation : les cibles W004/W008/W012/W016 sont
levées ; **W021 (preload) est un résidu assumé**, W005 se lèvera à l'activation
d'includeSubDomains, W009 disparaît avec la clé de prod forte.

## 🎯 Prochaine étape

**Ouverture de la Phase 3** — préparation de la commercialisation et évolutions
fonctionnelles, **à définir en revue stratégique**. Même méthode : revue
d'architecture avant tout code, une chose à la fois, tests, documentation, validation, commit.

## Rappels techniques

- Depuis C2 : poser `DJANGO_SECRET_KEY` avant toute commande Django en local
  (`$env:DJANGO_SECRET_KEY = "..."`). À reposer à chaque nouveau terminal.
- Variables d'environnement de production : voir `DEPLOIEMENT_o2switch.md` §4.
- Registre des anomalies : `2026-07-02_Anomalies_Restantes.md` — reste ouvert :
  **ACC-ZONE** (cohérence métier `?zone=<pk>`, faible sévérité).
- Étape 2 (ultérieure, hors Phase 2) : `MEDIA_ROOT` hors webroot + `X-Sendfile`.

## Méthode (inchangée depuis le début)
Une anomalie / un objectif = un lot. Revue d'architecture (sans code) → arbitrage DT →
sauvegarde → développement → tests → documentation → validation DT → commit.
Toute évolution doit être conforme à l'Architecture de Production v1, ou justifier un écart.
