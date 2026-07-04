# PSM2S — Rapport de clôture de la Phase 2 (Sécurité de production)

Document d'archive — Direction Technique
Date de clôture : 03/07/2026
Rédacteur : Lead Developer PSM2S

---

## 1. Objet du document

Ce rapport clôture officiellement la **Phase 2 — Sécurité de production** de PSM2S. Il constitue une pièce d'archive destinée à démontrer, à froid (audit, client, reprise dans plusieurs mois), ce qui a été accompli, les choix retenus et leurs justifications. Il n'est pas un document de travail quotidien (voir `POINT_DE_REPRISE.md` pour cela).

## 2. Contexte et objectifs initiaux

La Phase 2 faisait suite à la Phase 1 (sécurité applicative : correction des IDOR et anomalies associées). Son objectif : **rendre PSM2S apte à fonctionner durablement en mode production sécurisé**, en traitant les points critiques et élevés de l'audit relatifs à l'environnement de déploiement :

- **C1** — `DEBUG=True` en production (divulgation d'informations).
- **C2** — `SECRET_KEY` exposée en clair (compromission possible des sessions / jetons).
- **C3** — Médias (documents, signatures) servis sans authentification.
- **E4** — Transport non durci (cookies non `Secure`, absence de HSTS / redirection HTTPS).

Objectif transverse : ne plus corriger au coup par coup, mais **établir une architecture de production cohérente** dans laquelle chaque correctif s'inscrit.

## 3. Démarche

Avant tout développement, une **architecture de production cible (v1)** a été définie et validée, posant des principes directeurs : secure-by-default, configuration et secrets hors du code, serveur web pour le statique / Django pour les fichiers sensibles, barrière de déploiement, et — ajouté en cours de route — **pilotage de la sécurité de déploiement par variables dédiées, jamais dérivé de `DEBUG`**.

La méthode, héritée de la Phase 1, a été maintenue : une revue d'architecture sans code, un arbitrage explicite du Directeur Technique, un lot = un objectif, des tests, une documentation, une validation, puis un commit.

## 4. Lots réalisés

| Lot | Objet | Livrable principal |
|---|---|---|
| **INFRA-1** | Socle de configuration | `config/env.py` (`get_env`, `get_env_bool`), `.gitignore` durci, doc de déploiement o2switch |
| **C2** | Externalisation `SECRET_KEY` | `get_env_required` (sans fallback), retrait des secrets des `passenger_wsgi*`, procédure de rotation |
| **C3-1** | Desserte média protégée (documents) | Vue unique `media_protegee` + registre `media_access.py` (périmètre par établissement) |
| **C3-2** | Politique d'autorisation des signatures (S2) | Registre générique `autoriser()` (`par_perimetre` / `par_proprietaire`) ; perso = propriétaire strict |
| **C1** | Mise en service `DEBUG=False` | Activation du mécanisme INFRA-1 ; document de preuve (W018 absent) |
| **E4** | Durcissement du transport | Cookies `Secure`/`HttpOnly`/`SameSite`, HSTS progressif, `get_env_int` ; pilotage par `DJANGO_SSL` / `DJANGO_HSTS_SECONDS` |

Lots connexes de la Phase 1 rappelés pour mémoire : IDOR C4-1→C4-7, F9, E5, M11, BUG-TPL-01.

## 5. Choix d'architecture retenus et justifications

- **Configuration par variables d'environnement, secrets hors du code** (INFRA-1, C2). *Justification* : élimine les secrets versionnés, aligne dev / préproduction / production, cohérent avec l'hébergement (Passenger/cPanel o2switch).
- **Secure-by-default** : `DEBUG` défaut `False`, `SECRET_KEY` sans valeur de secours (échec explicite). *Justification* : l'état obtenu « sans rien faire » est le plus sûr.
- **Desserte média par une vue unique + registre central** (C3). *Justification* : point de contrôle unique, réutilisation de la primitive de périmètre de la Phase 1, extensibilité (ajouter un type de média = une ligne). `media_access.py` est devenu le composant central de sécurité des fichiers, pendant de `verifier_acces_etablissement` pour les objets.
- **Signature personnelle = propriétaire strict** (C3-2). *Justification* : donnée hautement sensible (identité graphique) ; aucune exception, même administrateur.
- **Sécurité de déploiement pilotée par variables dédiées, jamais par `not DEBUG`** (E4). *Justification* : découverte en revue que dériver `SECURE_SSL_REDIRECT` de `DEBUG` aurait provoqué des redirections 301 dans la suite de tests (qui tourne en `DEBUG=False`). Principe inscrit dans l'Architecture v1.
- **HSTS progressif, `preload` décliné** (E4). *Justification* : HSTS a des effets persistants côté navigateur ; une montée `300 → 86400 → 31536000` reste réversible pendant la validation. Le `preload` est un engagement durable (retrait en plusieurs mois) : refusé tant qu'il n'est pas délibérément souhaité.

## 6. Résultats obtenus

- **114 tests automatisés au vert** (0 échec), couvrant l'accès aux objets, la desserte média, les politiques de signature, et les helpers de configuration.
- `python manage.py check` **sans anomalie**.
- **Aucun secret dans le code** ; `SECRET_KEY` externalisée.
- **Aucun média servi anonymement** ; documents et signatures soumis à une politique d'autorisation centralisée.
- **`DEBUG=False`** vérifié en conditions de production (absence de `security.W018`).
- **Transport durci** câblé : les avertissements ciblés `check --deploy` (W004, W008, W012, W016) sont levés une fois l'activation faite.
- **Deux documents de référence permanents** : Architecture de Production v1 et Procédure de déploiement o2switch. **Historique Git propre** (un commit par lot).

### Lecture de `check --deploy` (mise au point importante)
`check --deploy` est un **outil d'aide à la décision**, pas un examen à 100 % de zéros. Après activation en production :
- **Levés** : W004 (HSTS), W008 (redirection SSL), W012 (cookie session), W016 (cookie CSRF) — objectifs techniques d'E4 ; W009 (clé) via la clé de production forte.
- **Résidus assumés et documentés** : **W005** (`includeSubDomains` — report volontaire jusqu'à validation HTTPS des deux domaines) et **W021** (`preload` — refusé par choix d'architecture).

## 7. Actions restant du ressort de l'exploitation

Ces opérations relèvent de la mise en production, non du développement :
1. Rotation des clés `SECRET_KEY` (prod + formation, distinctes).
2. Vérification du proxy HTTPS ; décision sur `SECURE_PROXY_SSL_HEADER`.
3. Activation `DJANGO_SSL=True`.
4. Montée progressive HSTS ; activation ultérieure d'`includeSubDomains`.
5. Mise en service `DEBUG=False` ; `collectstatic` ; `check --deploy` ; redémarrage Passenger.

Améliorations différées hors Phase 2 : **Étape 2** (déplacement de `MEDIA_ROOT` hors webroot + `X-Sendfile`) ; anomalie **ACC-ZONE** (cohérence métier `?zone=<pk>`, faible sévérité).

## 8. Conclusion

Au terme de la Phase 2, **PSM2S est prêt à fonctionner en mode production sécurisé** : configuration et secrets externalisés, mode debug désactivable en toute sûreté, données et documents protégés par une politique d'autorisation centralisée, et canal de transport durci de manière graduée et maîtrisée. La sécurité n'est plus une série de correctifs isolés mais un **cadre cohérent, documenté et testé**, qui limite l'apparition de nouvelles vulnérabilités.

La Phase 2 est **officiellement close** (côté développement). Les actions restantes sont opérationnelles et documentées. Le projet peut ouvrir la **Phase 3** (commercialisation et évolutions fonctionnelles) sur une base saine.

---

*Rapport établi le 03/07/2026. Documents de référence associés : Architecture de Production v1, Procédure de déploiement o2switch, comptes-rendus de lots (INFRA-1, C2, C3-1, C3-2, C1, E4), registre des anomalies.*
