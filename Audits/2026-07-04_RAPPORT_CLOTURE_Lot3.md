# PSM2S — Rapport de clôture du Lot 3 (Industrialisation)

Document d'archive — Direction Technique
Date de clôture : 04/07/2026
Rédacteur : Lead Developer PSM2S

---

## 1. Objet du document

Ce rapport clôture officiellement le **Lot 3 — Industrialisation** de PSM2S (hors L3.1a, volontairement reporté). Il constitue une pièce d'archive destinée à démontrer, à froid, ce qui a été accompli, les choix retenus et leurs justifications — sur le modèle du rapport de clôture de la Phase 2 (`2026-07-03_RAPPORT_CLOTURE_Phase2.md`).

## 2. Contexte et objectifs initiaux

Le Lot 3 faisait suite à la Phase 3 (Calendrier Réglementaire). Son point de départ était une question opérationnelle concrète : **comment mettre à jour proprement la plateforme de formation**, restée sur un code antérieur aux Phases 1 et 2. De ce besoin ponctuel a émergé un périmètre plus large, structuré en cinq sous-lots :

- **L3.1** — Resynchronisation de la plateforme formation.
- **L3.1a** — Durcissement HTTPS/HSTS sur formation (reporté, voir §7).
- **L3.2** — Rédaction de PROC-001 (procédure de déploiement).
- **L3.3** — Rédaction de PROC-002 (procédure de maintenance).
- **L3.4** — Architecture Core/Variantes et politique d'évolution.

## 3. Démarche

Un sous-lot actif à la fois, dans l'ordre où les besoins réels se sont présentés plutôt que selon un plan théorique préétabli : L3.1 (l'incident réel) a précédé L3.2 (la procédure qui en a été tirée), qui a précédé L3.3, avant que L3.4 ne pose la question, plus structurante, de l'architecture produit. Chaque sous-lot a suivi la méthode habituelle : revue avant code lorsque pertinent, validation du Directeur Technique à chaque étape, documentation proportionnée, tests, commit.

## 4. Sous-lots réalisés

| Sous-lot | Objet | Livrable principal | Statut |
|---|---|---|---|
| **L3.1** | Resynchronisation formation | Plateforme formation à jour (Phases 1+2+Lot 2 Calendrier), `.htaccess` définitif | Clos 04/07/2026 |
| **L3.2** | Procédure de déploiement | `PROC-001_Deploiement_Plateforme_PSM2S.md` | Clos 04/07/2026 |
| **L3.3** | Procédure de maintenance | `PROC-002_Maintenance_Instance_Client_PSM2S.md` | Clos 04/07/2026 |
| **L3.4** | Architecture Core/Variantes | Cartographie (L3.4.1), niveaux (L3.4.2), politique d'évolution `POLITIQUE-001` (L3.4.3), architecture technique (L3.4.4), implémentation (Phase 4, commit `a261a88`) | Clos 04/07/2026 |
| **L3.1a** | Durcissement HTTPS/HSTS formation | — | **Reporté**, hors clôture (voir §7) |

## 5. Choix d'architecture retenus et justifications

- **Fichiers spécifiques au serveur jamais versionnés** (`.htaccess`, `passenger_wsgi.py`, `settings_formation.py`). *Justification* : trois incidents réels sur L3.1 ont montré qu'écraser ces fichiers avec la version portable du dépôt casse le routage Passenger ou mélange les environnements.
- **Déploiement par transfert complet, jamais par diff Git ciblé**, tant qu'une plateforme n'est pas suivie par Git. *Justification* : l'état réel de la plateforme formation ne correspondait à aucun commit précis (dérive par dépôts FTP successifs) — un `git diff` ciblé s'est révélé structurellement insuffisant.
- **Git = source unique de vérité, sans exception** (principe renforcé dans PROC-002 à la demande du DT). *Justification* : aucune modification n'est considérée terminée tant qu'elle n'est pas committée, même sur un environnement qui n'est pas lui-même sous Git.
- **Mono-tenant par instance** (un client = un déploiement, une base dédiée), plutôt qu'une base partagée multi-clients. *Justification* : échelle visée (quelques établissements, pas des centaines) ; la complexité d'un filtrage applicatif permanent entre clients n'apporterait aucun bénéfice réel.
- **Séquence de décision Paramètre → Module commun → Généralisation au Core → Personnalisation métier en dernier recours** (`POLITIQUE-001`). *Justification* : protège le Core d'une fragmentation progressive au fil des demandes clients ; rend opérationnelle la Vision du projet (« enrichir la plateforme plutôt que multiplier des produits indépendants »).

## 6. Résultats obtenus

- Plateforme formation fonctionnelle et alignée sur la production (Phases 1+2, Lot 2 Calendrier).
- Trois documents permanents de référence : `PROC-001`, `PROC-002`, `POLITIQUE-001`, s'ajoutant à `DEPLOIEMENT_o2switch.md` et `IA_RULES.md`.
- Architecture Core/Variantes implémentée : Niveau 1 (Configuration — identité/branding par instance) et Niveau 2 (Eau, Commissions, DUERP, Accessibilité activables par instance), sans régression.
- **137/137 tests automatisés au vert**, commit `a261a88` poussé sur `main`.
- Aucun impact sur le comportement actuel de production/formation tant qu'aucune variable d'environnement n'est explicitement posée.

## 7. Actions restant du ressort de l'exploitation ou d'un lot futur

1. **L3.1a — Durcissement HTTPS/HSTS sur formation.** Volontairement reporté : traité comme un lot d'infrastructure autonome, à ouvrir lorsque le DT souhaitera renforcer l'environnement de formation — pas un prérequis au développement.
2. **Tickets/Interventions non câblé dans le mécanisme de modules activables** (L3.4 Phase 4) : le mécanisme est prêt, le câblage est différé en raison du couplage croisé avec DUERP/Accessibilité/Commissions.
3. **Dette technique de faible priorité** : avertissement `credential-manager-core is not a git command` lors des push Git — sans impact tant que l'authentification aboutit ; à corriger lors d'une remise à niveau de l'environnement Git local.
4. **Organisation et sauvegarde de `Documentation/` hors Git** — décision en cours, traitée séparément de ce rapport (voir `INDEX_DOCUMENTATION.md`).

## 8. Conclusion

Le Lot 3, ouvert pour répondre à un besoin opérationnel ponctuel (mettre à jour la plateforme formation), a produit un socle d'exploitation complet pour PSM2S : une méthode de déploiement éprouvée sur incident réel (L3.1), deux procédures permanentes (PROC-001, PROC-002), et — au-delà de l'objectif initial — la première architecture produit durable de PSM2S (L3.4), assortie d'une politique d'évolution qui protège le Core d'une fragmentation future. PSM2S dispose désormais d'une vision de produit, de règles d'architecture, de procédures d'exploitation, d'une politique d'évolution et d'une traçabilité des décisions — les conditions d'un logiciel qui peut évoluer plusieurs années sans perdre sa cohérence.

Le Lot 3 est **officiellement clos** (hors L3.1a, reporté). Le projet peut ouvrir la **Phase 4 fonctionnelle** sur un cadre d'architecture solide.

---

*Rapport établi le 04/07/2026. Documents de référence associés : `PROC-001`, `PROC-002`, `POLITIQUE-001`, `DEPLOIEMENT_o2switch.md`, comptes-rendus L3.1 à L3.4 (`Documentation/Developpements/`).*
