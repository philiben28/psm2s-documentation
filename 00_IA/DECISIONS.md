# PSM2S - DECISIONS

Registre des décisions du Directeur Technique / Product Owner.

Référencé par START_HERE.md. Ce fichier ne contient que des décisions
**actées** (validées en revue), pas des pistes ou des idées à l'étude.
Il se complète au fil des lots ; il ne remplace pas les comptes-rendus
détaillés de chaque lot (`Documentation/06_Historique/`, `Documentation/03_Développement/`),
qui restent la source de référence pour le détail technique.

---

## Phase 1 — Sécurité applicative

- **IDOR (C4-1 → C4-7)** : primitive unique de périmètre par établissement
  (`verifier_acces_etablissement`, `_get_etab_ids_autorises`), réutilisée
  partout (54 vues), y compris pour C3 (médias) en Phase 2.
- **F9 (FORM-PERIMETRE)** : filtrage des formulaires contre l'over-posting.
- **E5** : visibilité de la liste DUERP alignée sur `peut_tout_voir`.
- **ACC-ZONE** (ouverte, sévérité faible) : `?zone=<pk>` dans
  `accessibilite_action_ajouter` sans vérification de cohérence métier.
  Documentée, non corrigée dans C4-6, à traiter dans un lot d'affinage dédié.
- **Correctif post-Phase 1 — IDOR `registre_pdf`** (identifié et corrigé le
  04/07/2026, hors sweep C4-1→C4-7) : la vue utilisait encore
  `get_object_or_404(Etablissement, pk=pk)` sans vérification de périmètre —
  tout utilisateur connecté pouvait télécharger le PDF de registre de
  n'importe quel établissement. Découvert lors d'une revue de code ciblée
  (analyse P4-L2), pas d'un audit programmé. Corrigé par remplacement par
  `get_etablissement_ou_404(request.user, pk)`, identique au motif utilisé
  partout ailleurs dans le module Établissement ; 5 tests dédiés ajoutés
  (`RegistrePdfAccesTests`). Traité comme un correctif isolé, pas comme un
  lot fonctionnel : ce cas illustre qu'une revue ciblée peut encore révéler,
  après un audit approfondi, un point isolé oublié — la sécurité reste une
  propriété entretenue dans la durée, pas un état figé.

## Phase 2 — Sécurité de production

- **Architecture de Production v1** (validée DT, 02/07/2026) — référence
  permanente (`Audits/2026-07-02_Phase2_Architecture_Production.md`) :
  - Variables d'environnement : Passenger/cPanel o2switch en production
    (pas de `.env` en prod).
  - Settings : **Option A** — un seul `settings.py` piloté par l'environnement
    (pas de split base/dev/prod).
  - Statique : Apache + `collectstatic` (pas de WhiteNoise).
  - Médias : approche progressive — vue Django sécurisée d'abord (C3-1),
    `X-Sendfile` en Étape 2 ultérieure.
  - Formation (`formation.…`) : `DEBUG=False` aussi, aucune exception.
  - Base de données : reste SQLite pour l'instant (sujet non sécuritaire,
    traité plus tard en E6).
- **Sécurité de déploiement pilotée par variables dédiées** (principe ajouté
  en E4) : jamais dérivée de `DEBUG` (la suite de tests tourne en
  `DEBUG=False` ; dériver `SECURE_SSL_REDIRECT` de `not DEBUG` provoquerait
  des redirections 301 en test).
- **`SECRET_KEY` sans fallback** (C2) : absence = échec explicite au
  démarrage plutôt que clé faible silencieuse.
- **Signature personnelle = propriétaire strict** (C3-2) : aucune exception,
  même administrateur. Signatures DUERP/Accessibilité = périmètre établissement.
- **HSTS progressif, `preload` refusé** (E4) : montée `300 → 86400 → 31536000` ;
  `includeSubDomains` différé jusqu'à validation HTTPS des deux domaines ;
  `preload` non activé (engagement durable non souhaité pour l'instant).

## Phase 3 — Calendrier Réglementaire (priorité 1 du backlog)

- **Lot 1 (vue Mois)** validé PO le 02/07/2026 :
  - **Rendu 100 % serveur** (option A) : grille construite en Python
    (module standard `calendar`), aucune dépendance JavaScript.
  - **Seuils de couleur** paramétrables en tête de bloc : vert > 30 jours,
    orange entre 30 et 7 jours, rouge < 7 jours ou dépassé
    (`SEUIL_ORANGE_JOURS`, `SEUIL_ROUGE_JOURS`).
  - **Périmètre** : contrôles réglementaires uniquement (`ControleEtablissement`).
    Statuts `pas_obligation` et `non_concerne` exclus. Autres sources
    d'échéances (contrats, prescriptions, tickets) hors périmètre du Lot 1,
    à introduire une source à la fois dans des lots ultérieurs.
  - **Accès fiche contrôle** : réservé aux gestionnaires (admin/responsable/
    directeur) ; un factotum cliquant sur un événement est redirigé vers le
    dashboard (comportement existant, non modifié par le calendrier).
- **Lot 2 (vues Semaine et Jour)** développé le 03/07/2026, périmètre validé
  DT le 03/07/2026 :
  - Même vue `calendrier()`, granularité pilotée par le paramètre `vue=`
    (`mois`\|`semaine`\|`jour`), pas de nouvelle route.
  - Templates séparés par vue, avec légende / bandeau des retards / onglets
    factorisés en partials communs (décision d'implémentation, autonomie
    Lead Developer).
  - Semaine et Jour traités comme un seul lot fonctionnel (même patron de
    code que le Lot 1), périmètre limité à l'affichage : filtres et
    sources secondaires d'échéances restent hors lot.

## Lot 3 — Industrialisation (ouvert le 03/07/2026)

- **Sous-lots** : L3.1 Resynchronisation formation (clos 04/07/2026), L3.2
  PROC-001 (clos 04/07/2026), L3.1a Durcissement HTTPS formation (reporté),
  L3.3 PROC-002, L3.4 Architecture Core + Variantes, L3.5 Versioning
  (non ouverts). Un seul sous-lot actif à la fois.
- **Fichiers spécifiques au serveur jamais versionnés** (décidé suite aux
  incidents L3.1) : `.htaccess` (bloc Passenger CloudLinux),
  `passenger_wsgi.py` (contenu propre à chaque environnement, même nom de
  fichier sur le serveur bien que le dépôt porte des noms distincts),
  `config/settings_formation.py`. Règle formalisée dans
  `DEPLOIEMENT_o2switch.md` §3 sexies et `PROC-001`.
- **Déploiement par transfert complet, jamais par diff Git ciblé**, tant
  qu'une plateforme n'est pas suivie par Git (son état réel peut diverger
  de tout commit de référence). Recommandation de fond : faire passer
  chaque plateforme sous `Git Version Control` cPanel.
- **PROC-001** (`Documentation/08_Procedures/PROC-001_Deploiement_Plateforme_PSM2S.md`)
  est le document permanent de référence pour tout déploiement (nouveau
  serveur ou mise à jour), construit à partir de l'expérience réelle de
  L3.1 plutôt que d'une procédure théorique.
- **L3.1 officiellement clos, L3.1a reporté** (04/07/2026) : l'activation
  `DJANGO_SSL`/HSTS sur formation n'est pas ouverte immédiatement ; L3.3
  (PROC-002) priorisé avant, décision stratégique DT liée à la trajectoire
  multi-clients de PSM2S.
- **PROC-002** (`Documentation/08_Procedures/PROC-002_Maintenance_Instance_Client_PSM2S.md`,
  L3.3, clos 04/07/2026) : procédure de correctif ciblé sur une instance
  déjà déployée (identifier → vérifier l'état réel → corriger en local,
  périmètre strict → tester → déployer le correctif ciblé, en s'appuyant
  sur PROC-001 pour le mécanisme sans le dupliquer → vérifier → tracer).
  **Périmètre actuel volontairement limité** : PSM2S n'a pas encore
  d'architecture Core + Variantes (L3.4, non ouvert), donc « instance » =
  un environnement déployé dans son ensemble (formation, production) et
  non une variante cliente distincte. PROC-002 devra être révisée après
  L3.4.
- **Git = source unique de vérité (principe d'architecture)** (PROC-002,
  04/07/2026) : aucune modification de code n'est considérée comme
  terminée tant qu'elle n'est pas commitée dans le dépôt Git, sans
  exception — développement local, correctif de production, correctif de
  formation, future maintenance d'une variante cliente. S'applique même
  quand l'environnement corrigé n'est pas lui-même suivi par Git.
- **L3.1, L3.2, L3.3 clos** (04/07/2026) — socle d'exploitation de PSM2S
  (formation resynchronisée, déploiement reproductible, maintenance
  traçable). Prochain tournant identifié : **L3.4 — Architecture Core +
  Variantes**, décision d'architecture structurante (pas une procédure)
  conditionnant la gestion de plusieurs clients ; à concevoir avec soin.
- **L3.4.1 — Cartographie Core/Paramètre/Variante** (validée DT,
  04/07/2026) : cœur métier réglementaire = Core légitime (générique à
  tout ERP français). Identité/branding (nom, domaine, email, logo,
  couleurs) = aujourd'hui codés en dur, candidats à devenir Paramètre.
  Aucune fonctionnalité activable par instance aujourd'hui (gap identifié).
  Aucune variante de code identifiée à ce jour.
- **L3.4.2 — Niveaux de personnalisation** (validé DT, 04/07/2026) :
  hiérarchie Configuration (identité/branding) → Fonctionnalités
  activables (Eau, Commissions, DUERP, Accessibilité, Tickets/Interventions)
  → Personnalisations métier (aucun cas réel aujourd'hui, à ne pas
  concevoir par anticipation).
- **L3.4.3 — Politique d'évolution Core/Variante** (validée DT,
  04/07/2026), élevée au rang de document permanent : `POLITIQUE-001`
  (`Documentation/02_Architecture/POLITIQUE-001_Evolution_Core_Variante_PSM2S.md`).
  Séquence de décision à appliquer à toute demande : Paramètre → Module
  commun → Généralisation au Core → Personnalisation métier en dernier
  recours. Étape 4 (personnalisation métier) exige une validation DT
  systématique, sans exception ; toute demande arrivée en étape 3 ou 4 est
  tracée dans ce fichier.
- **L3.4.4 — Architecture technique Core/Variantes** (validée DT,
  04/07/2026) : **mono-tenant par instance** (un client = un déploiement,
  une base dédiée), aucune base partagée entre clients. Niveau 1
  (Configuration) : extension du mécanisme `config/env.py` existant +
  context processor pour l'identité/branding. Niveau 2 (Modules
  activables) : variable `DJANGO_MODULES_ACTIFS` + double garde (menu et
  accès vue), même logique de défense en profondeur que l'IDOR de Phase 1.
  Niveau 3 : aucun mécanisme construit, décision assumée (rare par
  construction). Déploiement d'une nouvelle instance client = `PROC-001`
  appliqué à un nouveau serveur, aucune nouvelle procédure.
- **L3.4 clos** (04/07/2026) — premier document d'architecture durable de
  PSM2S : fixe les règles d'évolution futures, pas seulement l'état actuel.
  Documents produits : L3.4.1 à L3.4.4 (`Documentation/03_Développement/`)
  et `POLITIQUE-001` (référence permanente).
- **L3.4 Phase 4 (Développement) commitée et poussée** (04/07/2026,
  commit `a261a88`) : 137/137 tests verts, aucune régression. Niveau 1
  (Configuration) et Niveau 2 (Eau, Commissions, DUERP, Accessibilité)
  opérationnels. Tickets/Interventions volontairement non câblé (couplage
  croisé avec les autres modules, cf. compte-rendu Phase 4) — mécanisme
  déjà prêt à l'accueillir en lot séparé.
- **Organisation documentaire** (04/07/2026) : sauvegarde mise en place
  d'abord — dépôt Git privé séparé `github.com/philiben28/psm2s-documentation`
  (distinct du dépôt de code), premier commit `1f51c85`, secret en clair
  (`07_ Ressources/la derniere clé secret_key.txt`) exclu via `.gitignore`.
  `Documentation/INDEX.md` devient le point d'entrée officiel du catalogue.
  Une fois la sauvegarde active, découverte que le DT avait déjà créé la
  structure `01_Livre_blanc` à `08_Procedures`, restée vide et invisible aux
  outils de recherche par fichiers — adoptée à son tour (commit `8051d88`) :
  tous les documents replacés dans cette arborescence, `Audits/` et
  `Developpements/` vidés. Les renvois internes des documents permanents
  (`DECISIONS.md`, `PROC-001`, `PROC-002`, `POLITIQUE-001`,
  `DEPLOIEMENT_o2switch.md`) mis à jour ; les comptes-rendus datés
  (archives) volontairement non retouchés.

## Phase 4 — Enrichissement fonctionnel (ouverte le 04/07/2026)

- **Convention de nommage** (04/07/2026) : les lots fonctionnels de la
  Phase 4 sont numérotés **P4-L1, P4-L2, …**, comme des jalons produit —
  plus lisible qu'une succession de commits, et facilite le lien entre
  développements, documents d'architecture, tests, décisions et
  démonstrations clients. Cycle attendu pour chaque lot : vérification du
  backlog/existant → analyse fonctionnelle → architecture détaillée courte
  → développement → tests → documentation → commit + mise à jour de ce
  fichier.
- **P4-L1 — Tableau de bord Directeur enrichi** (validé DT, développé et
  clos le 04/07/2026, commit `873da0c`) : score de conformité, 5 actions
  prioritaires, échéances proches (retard/aujourd'hui/semaine), indicateurs
  clés (contrôles en retard, prescriptions ouvertes, tickets critiques,
  contrats à échéance) ajoutés à `dashboard()`, réservés au rôle Directeur.
  **Aucune nouvelle logique métier** : moteur `registre/tableau_bord.py`
  (`collecter_conformite`) extrait de `tableau_de_bord()` et partagé par
  les deux vues — règle explicitement fixée par le DT pour ce lot, et
  première application réussie, sur un développement fonctionnel, de la
  discipline posée par `IA_RULES`/`POLITIQUE-001`/`PROC-001`/`PROC-002`.
  Question ouverte, non tranchée : un seul moteur de tableau de bord avec
  widgets par profil, vs deux pages distinctes — le partage du moteur
  garde cette option disponible sans l'imposer. 148/148 tests verts.
- **Méthode de sélection des lots Phase 4, au-delà du backlog écrit**
  (validée DT, 05/07/2026) : pour chaque nouveau lot, identifier le plus
  grand écart entre la promesse de la Vision et l'expérience vécue par un
  Directeur lors d'une démonstration de dix minutes, plutôt que de dérouler
  le backlog dans l'ordre. Adoptée comme méthode de travail pour les
  prochains lots fonctionnels.
- **P4-L2 — Lien direct vers la fiche depuis « Mes actions prioritaires »**
  (validé DT, développé et clos le 05/07/2026) : chaque ligne du widget
  ouvre désormais directement la fiche du contrôle ou du contrat concerné
  (`modifier_controle`/`modifier_contrat`), au lieu de la fiche générale de
  l'établissement — corrige un écart avec l'exigence écrite du backlog
  Priorité 3 (« chaque ligne doit ouvrir directement la fiche concernée »),
  découvert en rejouant l'expérience Directeur après P4-L1. **Principe
  d'architecture posé par le DT** : le moteur `collecter_conformite` reste
  agnostique de la navigation — il expose `cible_type`/`cible_pk` (identité
  de l'objet), jamais une URL ; c'est la couche de présentation (template)
  qui construit le lien. Garde le moteur réutilisable par un futur écran,
  une API ou une application mobile. 156/156 tests verts.
- **P4-L3 — Référentiel Prestataires, Étape A** (validé DT, développé le
  05/07/2026) : diagnostic — le nom d'un prestataire était déjà dupliqué en
  texte libre dans 4 modèles (`Contrat`, `Intervention`,
  `RealisationControle.organisme`, `AnalyseEau.laboratoire`), donc déjà une
  entité métier de fait. **Périmètre validé** : nouvelle entité
  `Prestataire` (nom, contact, téléphone, email, adresse, site web —
  volontairement minimal), branchée **uniquement sur `Contrat`** dans ce
  lot ; les 3 autres champs restent en texte libre, candidats à un futur
  lot si le besoin se confirme (conforme `POLITIQUE-001` : généraliser
  seulement quand le besoin est prouvé). **Migration en deux étapes**
  (recommandation DT, pour un retour arrière simple) : Étape A (ce lot) —
  `Contrat.prestataire_fk` coexiste avec le champ texte `prestataire`,
  migration de données avec dédoublonnage insensible à la casse
  (SOCOTEC/Socotec/socotec → un seul `Prestataire`), formulaires déjà
  branchés sur la FK ; Étape B (suppression du champ texte) différée,
  nouvelle validation DT explicite requise après confirmation en
  production et en formation. Aucun nouvel écran de gestion des
  prestataires dans ce lot (resterait à faire si le besoin de navigation
  se confirme). 170/170 tests verts.

---

*Fichier vivant : ajouter une entrée par décision structurante validée en
revue, sous la phase correspondante. Ne pas y consigner de décision non
actée.*
