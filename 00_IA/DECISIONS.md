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
- **Condition de passage à l'Étape B — reformulée par le DT** (05/07/2026) :
  non plus un délai d'attente, mais une validation technique (tests verts,
  migration en dev, migration confirmée sur formation, aucune
  `prestataire_fk` orpheline, revue du code encore lié au champ texte).
  Contexte explicite : PSM2S n'a pas encore de clients en production, le
  facteur limitant n'est plus le risque utilisateur mais la dette
  technique de deux champs parallèles. Dès validation technique complète,
  passage direct à l'Étape B, sans délai artificiel.
- **P4-L3, Étape A — validée sur la plateforme de formation** (05/07/2026) :
  migration appliquée (`0020_prestataire`, `0021_migrer_prestataires_contrats`),
  0 contrat orphelin (`prestataire_fk` vide avec texte non vide), tests
  fonctionnels concluants (dédoublonnage confirmé, création/modification
  de contrat, alerte de contrat à échéance toujours correcte sur le
  tableau de bord Directeur). Les 4 conditions posées par le DT sont
  satisfaites.
- **Anomalie découverte et corrigée pendant ce déploiement** (05/07/2026,
  hors périmètre de P4-L3 lui-même) : sur la plateforme de formation,
  `python manage.py migrate` sans variable explicite utilise
  `config.settings` (le défaut), alors que `passenger_wsgi.py` fixe
  `DJANGO_SETTINGS_MODULE=config.settings_formation` — deux bases
  distinctes. Conséquence : les migrations 0019 à 0021 n'avaient jamais
  été appliquées à la base réellement servie par Passenger, sans qu'aucune
  erreur ne le signale jusqu'à ce déploiement (aucune migration n'avait été
  créée depuis 0019). Corrigé : migration 0019 fakée après vérification
  que la contrainte `unique_together` visée n'existait déjà plus
  physiquement sur cette base (donc aucune perte réelle), puis 0020/0021
  appliquées normalement. **`PROC-001` (Étape 4) et `PROC-002` mis à jour**
  pour imposer la vérification de `DJANGO_SETTINGS_MODULE` avant toute
  commande `migrate` sur une instance à settings dédié.
- **P4-L3, Étape B — suppression du champ texte** (validée DT, développée
  le 05/07/2026) : `Contrat.prestataire` (CharField) supprimé,
  `prestataire_fk` devient l'unique source de vérité. **Périmètre tenu
  strictement** aux trois catégories fixées par le DT : suppression du
  champ + mise à jour du modèle ; adaptation des 8 points de consommation
  identifiés lors de la revue (ni plus, ni moins) ; adaptation des tests
  existants (une classe de tests devenue obsolète retirée, un test de
  verrou de clôture ajouté). Aucun raccordement d'`Intervention`,
  `RealisationControle` ou `AnalyseEau` — ils gardent leur propre lot
  futur (`POLITIQUE-001`). Recherche globale confirmée : aucune référence
  au champ texte ne subsiste hors migrations historiques (0007-0021,
  jamais retouchées). 169/169 tests verts.
- **P4-L3 — modèle de migration progressive** (05/07/2026) : le DT retient
  la séquence suivie (nouvelle entité → migration de données → validation
  technique → validation sur instance déployée → suppression de l'ancien
  champ) comme méthode de référence pour toute future évolution de schéma
  touchant des données existantes.
- **Règle de décision PROC-002 vs PROC-001** (05/07/2026) : un déploiement
  ciblé (PROC-002) suppose que l'instance cible est déjà synchronisée avec
  le dépôt, à l'exception du correctif déployé. La resynchronisation de
  formation a révélé que ce n'était pas le cas (`registre/tableau_bord.py`,
  introduit par P4-L1, absent de la plateforme — P4-L1, P4-L2 et le
  correctif IDOR n'y avaient jamais été déployés). **Règle retenue** : si
  la synchronisation ne peut pas être démontrée avec certitude, appliquer
  PROC-001 (resynchronisation complète) plutôt que de reconstituer un
  delta manuellement — même leçon que L3.1, appliquée cette fois au choix
  de procédure. `PROC-002` mis à jour en conséquence.
- **Anomalies découvertes lors de la resynchronisation formation**
  (05/07/2026, hors périmètre de P4-L3, sans lien avec ce lot) :
  - **DEBUG-FORMATION** : `config/settings_formation.py` (fichier serveur,
    hors Git) redéfinissait `DEBUG = True` en dur, écrasant le défaut sûr
    de `settings.py` — faille de sécurité active, jamais détectée faute
    d'avoir exécuté `check --deploy` sous le bon `DJANGO_SETTINGS_MODULE`
    avant ce jour. Corrigée sur le serveur (ligne supprimée, hérite du
    défaut `False`) ; `security.W018` confirmé disparu après correction.
  - **DB-NOM-FORMATION** : la base réellement utilisée par formation est
    `db_formation.sqlite3` (définie dans `settings_formation.py`), pas
    `db.sqlite3` — les premières sauvegardes de la journée portaient sur
    le mauvais fichier. Base réelle sauvegardée a posteriori, taille
    vérifiée identique.
  - **`PROC-001` complété** : nouvelle Étape 0.2 (vérification du module
    de settings réel, du nom de la base, et de `DEBUG` avant toute
    sauvegarde/migration sur une instance à settings dédié) — aurait permis
    de détecter ces deux anomalies dès le début.
- **Correctif dédié — Incohérence Interface/Permissions – Contrats**
  (05/07/2026, découvert pendant la vérification fonctionnelle du
  resync formation, hors P4-L3) : `detail_etablissement.html` masquait le
  bouton « Nouveau contrat » et les icônes « Modifier »/« Supprimer » des
  contrats derrière `{% if user.est_responsable or user.est_admin %}`,
  alors que les vues `nouveau_contrat`/`modifier_contrat`/`supprimer_contrat`
  sont toutes `@gestionnaire_requis` (admin, responsable_securite,
  **directeur**) — un Directeur avait donc le droit d'accès (accessible par
  URL directe) mais aucune affordance dans l'interface. Pas une urgence de
  sécurité, mais le type d'incohérence pouvant dérouter un client en
  démonstration. Corrigé en ajoutant `or user.est_directeur` aux 3
  occurrences concernant les Contrats uniquement (bouton « Nouveau
  contrat », icônes « Modifier »/« Supprimer », lien vide « Ajouter le
  premier contrat ») — les 4 autres occurrences du même motif dans le
  fichier (bâtiments, commissions) sont **hors périmètre** de ce correctif
  et laissées inchangées, conformément à POLITIQUE-001 (ne pas généraliser
  par anticipation). Un test de non-régression dédié ajouté
  (`ContratAccesTests.test_directeur_voit_le_bouton_modifier_un_contrat`).
  Traité comme un correctif isolé, distinct de P4-L3 et de P4-L2.
- **Sortie de la période transitoire PROC-001 — formation à nouveau
  synchronisée** (05/07/2026) : à compter de la resynchronisation complète
  du 05/07/2026 (resync HEAD, migrations appliquées, correctif IDOR
  validé, `DEBUG=True` corrigé, vraie base identifiée, référentiel
  Prestataires validé), la plateforme de formation est de nouveau
  considérée comme **synchronisée avec le dépôt Git**, hors fichiers
  spécifiques au serveur documentés dans `PROC-001` (Étape 0). Les futurs
  déploiements correctifs peuvent utiliser `PROC-002` tant que cette
  synchronisation reste maintenue. Critère de sortie de cette hypothèse
  (donc de retour à `PROC-001`) : voir la précondition ajoutée à
  `PROC-002` (« Règle de décision — PROC-002 ou PROC-001 ? »).
- **Clôture formelle — resynchronisation formation du 05/07/2026 et
  P4-L3** : la checklist de vérification post-déploiement (`PROC-001`
  Étape 6) est intégralement déroulée sur formation, tous points confirmés,
  y compris le périmètre par rôle (Directeur Roger Hanin : accès limité à
  IME Le Tramplin, aucun autre établissement visible). P4-L1, P4-L2, le
  correctif IDOR `registre_pdf`, P4-L3 (Étapes A et B) et le correctif
  Contrats sont donc considérés comme **formellement clos, en développement
  comme sur formation**.

## P4-L4 — Référentiel partagé des partenaires techniques (ouvert le 05/07/2026)

- **Besoin métier identifié** : au-delà de la simple identification du
  titulaire d'un contrat (P4-L3), l'organisation possède déjà une
  connaissance des prestataires qui interviennent dans plusieurs
  établissements — connaissance aujourd'hui non capitalisée (le Directeur
  repart de zéro : recherche, carnet d'adresses, mémoire des collègues).
  PSM2S doit exposer cette connaissance déjà présente dans les données
  existantes (`Contrat.etablissement` + `Contrat.prestataire_fk`), pas la
  recréer.
- **Découpage retenu** (POLITIQUE-001 — plusieurs petits lots, pas un
  module massif) :
  - **P4-L4** : fiche Prestataire en lecture seule (liste des prestataires,
    fiche par prestataire avec coordonnées + établissements où il
    intervient + type de contrôle), lien direct depuis la fiche Contrat.
    Aucune migration : uniquement des vues/templates sur les relations
    existantes.
  - **P4-L5** (à ouvrir après retour d'usage de L4) : création/modification
    d'un Prestataire depuis un écran dédié ; remplacement du champ texte
    libre du formulaire Contrat par une recherche parmi les prestataires
    existants.
  - **P4-L6** (candidat, non garanti) : suggestion proactive de
    prestataires pertinents à la création d'un contrat ou d'un
    établissement — à confirmer seulement si le besoin se vérifie après
    L4/L5.
  - Hors périmètre, différé : catégorisation par spécialité (le type de
    contrôle du contrat suffit aujourd'hui), raccordement d'`Intervention`,
    `RealisationControle`, `AnalyseEau` (POLITIQUE-001, inchangé),
    évaluation/historique de performance (non demandé).
- **Décision de périmètre/sécurité (05/07/2026)** : la vue croisée « ce
  prestataire intervient aussi dans tel autre établissement » pose une
  question de périmètre au regard de la discipline IDOR (C4-1→C4-7) — un
  Directeur ne doit pas apprendre l'existence ou le nom d'un établissement
  hors de son périmètre via cette vue. **Décidé** : la vue croisée complète
  (liste des autres établissements) est réservée aux rôles ayant
  `peut_tout_voir` (`admin`, `responsable_securite`, y compris les
  utilisateurs Directeur Général et Directeur Général adjoint, déjà créés
  avec le rôle `responsable_securite` — aucun nouveau rôle nécessaire dans
  `ROLE_CHOICES`). Un Directeur ne voit, pour un prestataire donné, que sa
  propre relation contractuelle (son ou ses établissements), pas la liste
  des autres établissements clients de ce prestataire.
- **Feu Vert n°3 accordé (05/07/2026)**, après revue fonctionnelle du plan
  technique. Points validés sans réserve : réutilisation intégrale de
  l'existant (aucun nouveau modèle, aucune migration), permissions
  (`get_prestataire_ou_404`, même famille que `get_etablissement_ou_404`).
  Clarification demandée et apportée avant le feu vert : `Contrat.type_controle`
  est une `ForeignKey` propre au modèle `Contrat` (catalogue `TypeControle`,
  même référentiel que `ControleEtablissement`), mais **sans aucune relation**
  avec `ControleEtablissement`/`RealisationControle` — vérifié dans le code.
  C'est un attribut descriptif du contrat (« quel domaine réglementaire ce
  contrat couvre-t-il »), pas un pointeur vers un événement de contrôle
  réalisé. La chaîne affichée sur la fiche Prestataire est donc bien
  `Prestataire → Contrat → Établissement` (avec le type de contrôle comme
  attribut du contrat), sans confusion entre contrat de maintenance et
  contrôle réglementaire.
  Trois ajustements de cadrage retenus avant développement : vocabulaire
  d'interface (menu « Partenaires », titre d'écran « Référentiel des
  partenaires », fiche continuant d'afficher « Prestataire » — aucun
  changement de modèle ni de nom de classe) ; compteur de la liste exprimé
  en établissements ET contrats (« Intervient dans N établissements —
  M contrats ») plutôt qu'en contrats seuls ; ajout des dates « Premier
  contrat » et « Dernière intervention contractuelle » sur la fiche
  (agrégation `Min`/`Max` sur les contrats visibles, aucune nouvelle donnée).
- **P4-L4 — développé, testé, documenté, commité (05/07/2026)** : 9 tests
  dédiés, 179/179 verts avec la suite complète. Écrans livrés : liste des
  partenaires (`registre:liste_prestataires`) et fiche
  (`registre:detail_prestataire`), lien direct depuis la fiche Contrat.
  Périmètre vérifié par test : un admin voit tous les établissements
  clients d'un prestataire et les compteurs globaux ; un Directeur ne
  voit que sa propre relation contractuelle et reçoit un 404 (jamais 403)
  sur un prestataire hors de son périmètre.
- **P4-L4 clos, dev et formation (05/07/2026)** : déployé sur formation via
  `PROC-002` (7 fichiers transférés — `views.py`, `permissions.py`,
  `urls.py`, `base.html`, `detail_etablissement.html`,
  `prestataires_liste.html`, `prestataire_detail.html` — redémarrage
  Passenger nécessaire, fichiers `.py` modifiés). Checklist de vérification
  (`PROC-001` Étape 6/`PROC-002` Étape 6) déroulée et confirmée : menu
  Partenaires visible pour admin/responsable/directeur ; fiche et liste
  correctes ; lien depuis la fiche Contrat fonctionnel ; **périmètre par
  rôle confirmé en conditions réelles** — le Directeur Roger Hanin (IME Le
  Tramplin) ne voit dans la liste Partenaires que les prestataires reliés
  à ses propres contrats, et sur la fiche d'un prestataire partagé ne voit
  que sa propre ligne, aucun autre établissement.
- **Gap constaté à l'usage (05/07/2026), immédiatement après P4-L4** :
  `Prestataire` n'est exposé dans **aucune** interface de saisie —
  ni écran PSM2S (hors périmètre volontaire de P4-L4), ni Django admin
  (jamais enregistré dans `admin.py`). Un partenaire créé implicitement
  depuis le formulaire Contrat (`get_or_create_normalise`, nom seul) n'a
  donc aujourd'hui aucun moyen d'être complété (contact, téléphone, email,
  adresse, site web) autrement que par une modification directe en base.
  **Décision** : ne pas utiliser le Django admin comme solution
  fonctionnelle, même provisoire — contraire à la vision PSM2S où chaque
  objet métier important se gère depuis l'application elle-même, pas via
  un outil technique. Ne pas reporter indéfiniment ce point non plus.
  **P4-L5 est élevé au rang de priorité immédiate après clôture complète
  de P4-L4** (dev + formation) : écran de création/modification dédié,
  et remplacement du champ texte libre du formulaire Contrat par une
  recherche parmi les prestataires existants — cadrage déjà posé plus haut
  dans cette section, inchangé.
- **Décision d'architecture — modèle à trois niveaux Entreprise / Agence /
  Contact (05/07/2026), pendant le cadrage de P4-L5.** L'exemple SOCOTEC
  (plusieurs agences, plusieurs techniciens, coordonnées différentes par
  agence/technicien) a révélé que le besoin réel est plus riche qu'un
  simple CRUD sur `Prestataire` : trois niveaux d'information distincts —
  l'entreprise (unique dans PSM2S), l'agence (coordonnées locales), le
  correspondant/contact (personne physique, éventuellement rattaché à un
  contrat précis).
  **Rejeté explicitement** : laisser chaque établissement créer sa propre
  fiche de contact/technicien pour le même correspondant. Ce serait
  recréer, au niveau du contact, exactement le problème de duplication
  que le référentiel `Prestataire` (P4-L3/P4-L4) cherche à éliminer au
  niveau de l'entreprise (ex. « Jean Dupont », « Jean DUPONT »,
  « J. Dupont » saisis séparément par plusieurs Directeurs).
  **Décision d'architecture actée** : *le modèle `Prestataire` représente
  une entreprise, pas une agence ni une personne.* Cette clarification
  s'applique à toute évolution future du référentiel.
  **Décidé pour P4-L5** : rester volontairement simple — une seule fiche
  Prestataire (entreprise), le champ `contact_nom` existant faisant office
  de « contact principal » (couvre l'essentiel des cas actuels, sans
  nouveau modèle). Le modèle Agence/Contact à trois niveaux n'est **pas**
  développé maintenant (impliquerait nouveau modèle, migrations,
  formulaires, permissions, vues, recherche — hors périmètre de P4-L5).
  Inscrit au backlog comme lot futur « Contact Partenaire » (cf.
  `PRODUCT_BACKLOG.md`), à ouvrir seulement quand le besoin sera mûr —
  cohérent avec POLITIQUE-001.
- **Révision du cadrage P4-L5 — modèle à deux niveaux Mémoire de
  l'organisation / Mémoire de l'établissement (05/07/2026), remplace la
  décision « `contact_nom` suffit » ci-dessus.** En creusant l'exemple
  SOCOTEC (plusieurs agences, plusieurs techniciens, coordonnées propres à
  chacun), il est apparu qu'un seul champ `contact_nom` sur `Prestataire`
  ne suffit pas : deux établissements différents ont besoin de garder,
  chacun, leur propre correspondant (nom, téléphone, email, notes libres —
  « toujours appeler après 8h30 », « passe le mardi »), sans que cette
  information soit partagée ni écrasée par un autre établissement.
  **Rejeté explicitement** : laisser chaque établissement créer sa propre
  fiche de contact pour le même prestataire sans structure dédiée —
  recréerait la duplication (Jean Dupont / Jean DUPONT / J. Dupont) que le
  référentiel `Prestataire` cherche à éliminer.
  **Décision d'architecture actée** : nouvel objet `CorrespondantLocal`,
  un par couple (`Prestataire`, `Etablissement`) — la mémoire opérationnelle
  d'un établissement avec ce prestataire (« le Post-it »), strictement
  distincte de la mémoire de l'organisation (`Prestataire` = référentiel
  partagé, entreprise uniquement, inchangé). Chaque établissement gère
  librement le sien ; jamais visible par un autre établissement (sauf
  admin/responsable_securite, `peut_tout_voir`, cohérent avec le reste de
  PSM2S).
  **Décision d'ergonomie** : une seule fiche visible côté utilisateur —
  le Directeur ne doit jamais avoir conscience qu'il existe deux objets
  distincts en base. L'écran « Nouveau partenaire » combine la création du
  référentiel (si le prestataire n'existe pas encore, dédoublonné via
  `get_or_create_normalise` comme aujourd'hui) et son propre correspondant
  local, en une seule soumission. Point d'entrée toujours scopé à un
  établissement (URL `/etablissement/<etab_pk>/partenaire/nouveau/`, même
  motif que `nouveau_contrat`) — jamais depuis `liste_prestataires`
  (écran transverse, pas rattaché à un établissement). Pour un prestataire
  déjà référencé, un encart « Mon correspondant » est ajouté directement
  sur `detail_prestataire`, avec son propre point d'édition.
  **Permissions, simplifiées par cette séparation** : modification du
  référentiel partagé réservée à admin/responsable_securite une fois créé
  (nouveau décorateur, cf. code) ; création d'un nouveau prestataire
  (avec son correspondant local) ouverte à tout `gestionnaire_requis`,
  comme aujourd'hui ; correspondant local géré librement par
  l'établissement concerné (`verifier_acces_etablissement`, même
  garde-fou que partout ailleurs). Plus besoin de la règle conditionnelle
  envisagée initialement (« admin seul si le prestataire est partagé par
  plusieurs établissements ») : elle disparaît, remplacée par cette
  séparation nette des deux objets.
  **Feu Vert accordé (05/07/2026).**
- **Renumérotation Phase 4** (05/07/2026, conséquence directe de la
  révision ci-dessus) : **P4-L5** = gestion complète d'un partenaire
  (référentiel + correspondant local, un seul écran, décrit ci-dessus).
  **P4-L6** = suggestions intelligentes (remplacement du champ texte libre
  du formulaire Contrat par une sélection parmi les prestataires existants,
  détection de doublons) — anciennement une partie de l'ancien P4-L5.
  **P4-L7** = Widget Directeur (les actions prioritaires), non cadré,
  renuméroté depuis l'ancien candidat « suggestion proactive » P4-L6.
  Le futur « Contact Partenaire » (plusieurs correspondants, niveau
  Agence) reste au backlog, non numéroté, et vient maintenant compléter
  `CorrespondantLocal` plutôt que le remplacer.
- **P4-L5 — développé, testé, migration appliquée (05/07/2026)** :
  192/192 tests verts (179 existants + 13 dédiés — permissions référentiel
  vs correspondant local, périmètre par établissement, dédoublonnage à la
  création, non-duplication du couple prestataire/établissement,
  affichage filtré sur la fiche). Nouvelle table `CorrespondantLocal`,
  aucune donnée existante à transformer. Reste à déployer sur formation
  (`PROC-002`, avec l'étape migration de `PROC-001`) et à vérifier avant
  clôture formelle.
- **P4-L5 clos, dev et formation (05/07/2026)**. Migration
  `0023_correspondantlocal` appliquée et confirmée (`showmigrations`).
  Vérification fonctionnelle (Étape 6) confirmée : icône « Modifier »
  référentiel (admin/responsable_securite), création combinée « Nouveau
  partenaire » (Directeur), périmètre du correspondant local confirmé en
  conditions réelles (Roger Hanin ne voit que sa propre ligne sur un
  partenaire partagé ; admin voit les deux).
  **Incident de déploiement rencontré et corrigé** : les deux nouveaux
  templates (`prestataire_form.html`, `correspondant_local_form.html`)
  avaient été omis du transfert initial (seuls les fichiers déjà existants
  à écraser avaient été copiés) — `Server Error 500`
  (`TemplateDoesNotExist`) sur `modifier_prestataire` et
  `correspondant_local`, et bouton « Nouveau partenaire » sans effet.
  Diagnostiqué sans navigateur, via `manage.py shell` +
  `RequestFactory` appelant directement les vues (plus rapide que la
  recherche du bon fichier de log applicatif — les logs `~/logs/` de
  cPanel ne contiennent que l'accès Apache, pas la trace Python).
  **Leçon retenue pour les prochains lots** : lors d'un transfert
  PROC-002/PROC-001, vérifier explicitement la présence des fichiers
  **nouveaux** (pas seulement les modifiés) sur l'instance cible — un
  transfert peut réussir silencieusement en ne copiant que les fichiers
  déjà connus de part et d'autre.

---

## Correctif post-P4-L5 — Signature électronique DUERP (24/08/2026)

Découvert en préparant la vidéo de démonstration (compte `demo_directeur`
tentant de signer le DUERP de démo créé pour le tournage) : `Server Error
500` systématique sur `duerp_signer`, jamais testé en conditions réelles
jusqu'ici. Deux bugs indépendants trouvés et corrigés dans `views.py`,
diagnostiqués sans navigateur via `manage.py shell` + `RequestFactory`
(même méthode que l'incident P4-L5 du 05/07/2026) :

1. `_copier_signature` écrivait le fichier de signature vers un chemin
   **relatif** (`'media/...'`) au lieu de `settings.MEDIA_ROOT` — ne
   fonctionnait que par coïncidence en développement local (le répertoire
   de travail du process n'est pas garanti identique à la racine du
   projet sous Passenger).
2. `duerp_signer` utilisait `models.Q(...)` sans que `models` soit
   importé dans le fichier (ni localement) — `NameError` immédiat, quel
   que soit l'environnement.

Corrigé et déployé sur formation le 24/08/2026, vérifié par le
diagnostic direct (`OK — statut réponse : 302`) puis par une signature
réelle dans l'application. **À reporter sur l'instance production** —
le bug n'est pas spécifique à formation, il touchera n'importe quel
directeur/responsable tentant de signer un DUERP en production tant que
le correctif n'y est pas déployé.

---

## Méthodologie de préparation des données de démonstration (28/08/2026)

Constat d'origine : le jeu de données démo initial (P4, script `demo_video_seed.py`
du 21/08/2026) avait été enrichi au fil de l'eau pendant le tournage d'une
vidéo commerciale, sans audit préalable — deux doublons silencieux sont
apparus (`VisiteCommission` et `Intervention`), causés par une clé
`get_or_create` construite sur une **date relative** (`today + timedelta`)
recalculée différemment à chaque exécution du script à des jours
différents.

**Décision de méthode (DT, validée)** : toute préparation ultérieure de
données de démonstration suit désormais un processus en 4 étapes,
jamais d'exécution directe :
1. Audit en lecture seule de l'existant (script dédié, aucune écriture).
2. État des lieux formel : ce qui est déjà exploitable, ce qui manque
   réellement (pas de remplissage par défaut).
3. Proposition détaillée avant toute écriture — pour chaque objet :
   valeur actuelle, valeur proposée, justification, impact sur le
   scénario vidéo.
4. Exécution uniquement sur feu vert explicite, et jamais avant la date
   réelle du tournage quand des échéances relatives sont en jeu (sinon
   nouvelle dérive garantie).

**Règle technique retenue** : dans un script de seed/correction
idempotent, la clé de `get_or_create` ne doit **jamais** contenir une
valeur calculée par rapport à `today` — utiliser un champ stable
(titre, nom, année) comme clé, et ne mettre les dates relatives que
dans les `defaults` (jamais recalculées sur un enregistrement déjà
existant, ce qui est le comportement voulu).

Appliqué le 28/08/2026 à deux scripts :
- `correction_donnees_demo.py` : nettoyage des deux doublons identifiés
  (conserve l'enregistrement le plus récent), recalcul des échéances de
  3 contrôles des Tilleuls pour raconter un scénario crédible (une
  échéance en retard, une proche, une à venir — pas un décalage
  mécanique de toutes les dates), passage du niveau factotum de Karim
  Belhadj à 3, affectation de Karim comme responsable du ticket
  ascenseur.
- `extension_quotidien_tilleuls.py` : 4 cas de maintenance quotidienne
  (fontaines à eau, bande podotactile, éclairage, plomberie) pour
  montrer que PSM2S couvre aussi le quotidien du bâtiment, pas
  seulement les contrôles réglementaires. Nouveau prestataire fictif
  « AMEB Multiservices » (artisan tous corps d'état), volontairement
  distinct des organismes de contrôle réglementaire déjà en place. Un
  cas volontairement laissé « en cours » (pas clôturé) pour montrer le
  suivi d'une intervention non terminée, pas seulement des clôtures.

`correction_donnees_demo.py` n'a pas été exécuté au moment de la rédaction
de cette entrée — feu vert donné sur le principe, exécution prévue le jour
du tournage. `extension_quotidien_tilleuls.py` a depuis été remplacé (voir
entrée du 03/09/2026 ci-dessous) avant d'avoir été exécuté.

**Point hors périmètre identifié pendant l'audit** : 5 établissements
non liés à la démo (codes non préfixés `DEMO-`) coexistent dans la
base formation. Confirmé fictifs par Phil le 28/08/2026, mais restent
hors périmètre de l'environnement de démonstration — aucun script de
démo ne doit jamais les référencer, y compris indirectement.

---

## Incident de sécurité — SECRET_KEY production exposée publiquement (03/09/2026)

Découvert dès la première étape de vérification en conditions réelles de
l'audit sécurité ouvert le 28/08/2026 (script `diagnostic_hebergement.sh`,
lecture seule) : un fichier `Cle.txt` présent à la racine du dossier
**formation** (donc servi publiquement, `Options -Indexes` désactivé mais
aucune règle bloquant l'accès direct à un fichier connu) répondait
**HTTP 200** sur `https://formation.psm2s.pbci-conseils.fr/Cle.txt`.

Son contenu : une ancienne version de `passenger_wsgi.py` **de la
production** (`/home/roda4402/psm2s_v2`, `config.settings`), avec
`DJANGO_SECRET_KEY` écrite en clair dans le code (motif antérieur à la
décision C2 — « SECRET_KEY sans fallback », Phase 2 — qui visait
justement à sortir la clé du code source). Contrairement à ce que le
commentaire de `passenger_wsgi.py` de formation laissait penser (« Lot
C2 : plus aucun secret en clair »), la vérification en direct via cPanel
(Setup Python App → `psm2s_v2` → Environment variables → aucune entrée)
a confirmé que la production lisait encore sa clé secrète **écrite en
dur dans son propre `passenger_wsgi.py`**, jamais migrée vers le
mécanisme par variable d'environnement contrairement à formation.

**Risque** : `SECRET_KEY` signe les sessions, les jetons CSRF et les
liens de réinitialisation de mot de passe Django — une clé compromise
permet en théorie de forger une session valide sans mot de passe.
Gravité retenue : critique.

**Corrigé le 03/09/2026, par Phil, en suivant une procédure guidée pas à
pas** (pas de session Claude Code directe, aucun accès bash/SSH côté
assistant durant tout l'incident) :
1. Suppression de `Cle.txt` du dossier formation.
2. Nouvelle clé générée via `get_random_secret_key()` (venv formation).
3. `passenger_wsgi.py` de **production** édité en local (FileZilla +
   Bloc-notes, avec copie de sauvegarde locale avant modification) pour
   remplacer la valeur de `DJANGO_SECRET_KEY`.
4. Redéploiement du fichier, redémarrage de l'application `psm2s_v2`
   via cPanel.
5. Vérifié : `https://psm2s.pbci-conseils.fr/` répond normalement après
   redémarrage.

**Point ouvert, non traité dans l'urgence** : la production n'est
toujours pas passée au mécanisme par variable d'environnement (elle a
seulement reçu une nouvelle valeur, toujours en dur dans le code) — un
futur lot devra aligner `psm2s_v2/passenger_wsgi.py` sur le motif déjà
en place côté formation, pour que ce type d'incident ne puisse plus se
reproduire par nature. À inscrire au backlog technique.

**Autres fichiers de sauvegarde/archives repérés dans le même dossier
formation pendant ce diagnostic** (`db_formation.sqlite3`,
`db.sqlite3`, plusieurs `.bak` et `.zip`, `backup_db.sh`) : **exposition
confirmée également** (tous répondaient HTTP 200, base de données
complète comprise, avec mots de passe hashés des comptes). **Corrigé le
03/09/2026** par ajout d'une règle Apache dans `.htaccess` de formation :
```
<FilesMatch "(\.sqlite3|\.bak|\.zip|\.sh|\.log|\.sql)">
    Require all denied
</FilesMatch>
```
Vérifié : les 9 fichiers testés répondent désormais 404 (au lieu de
200) ; l'application continue de fonctionner normalement. **Incident de
méthode pendant la correction** : une première tentative via FileZilla +
Bloc-notes Windows a échoué silencieusement — Notepad ne gère pas les
fins de ligne Unix du fichier serveur, tout le bloc ajouté s'est
retrouvé fusionné sur une seule ligne de commentaire, donc inactif (sans
casser le site). Corrigé en éditant `.htaccess` directement en SSH via
`cat >> .htaccess << 'EOF' ... EOF`, qui garantit des fins de ligne
correctes. **Vérifié et corrigé également sur la production (`psm2s_v2`), même
jour** : exposition confirmée plus large qu'en formation — `.htaccess`
de production totalement vide (0 octet, aucune protection), fichiers
exposés incluant `db.sqlite3` (base **actuelle** de production),
`config/settings.py.bak`, `passenger_wsgi.py.bak`, et l'intégralité du
dossier `backups/` (9 sauvegardes quotidiennes complètes,
`db_2026-08-26` à `db_2026-09-03`). Corrigé par création d'un
`.htaccess` (Options -Indexes + même règle `FilesMatch`) directement en
SSH. Vérifié : tous les fichiers testés (bases, sauvegardes, `.bak`,
et les fichiers `.py` eux-mêmes — `passenger_wsgi.py`,
`config/settings.py`, `manage.py`) répondent désormais 404, y compris
le listage du dossier `backups/`. Site de production confirmé
fonctionnel après correction.

**Bonne nouvelle découverte à cette occasion** : la production dispose
déjà d'une sauvegarde automatique quotidienne fiable (cron `backup_db.sh`
à 2h, 9 jours d'historique glissant observés) — point positif à intégrer
tel quel dans la fiche de synthèse sécurité.

**Investigation `DEBUG = True` sur production — cause identifiée
(03/09/2026)** : `config/settings.py` déployé sur `psm2s_v2` n'est **pas**
la version suivie par le dépôt Git ni celle déployée sur formation, mais
une version ancienne, antérieure à toute la discipline de sécurité posée
en Phase 2 — pas d'imports `get_env`/`get_env_bool`/`get_env_required`,
`SECRET_KEY` avec un filet de secours faible en dur dans le code
(`os.getenv('DJANGO_SECRET_KEY', 'django-insecure-remplacer-cette-cle-en-production')`,
contraire à la décision C2), `DEBUG = True` en dur avec le commentaire
« Passer à False en production réelle » jamais suivi d'effet, et une
entrée `ALLOWED_HOSTS` corrompue (un lien Markdown `[www...](https://...)`
collé tel quel au lieu du nom de domaine `www.psm2s.pbci-conseils.fr`).
**Constat retenu** : la production n'a jamais reçu la mise à jour de
sécurité appliquée à formation le 05/07/2026 (resynchronisation L3.1) ;
les deux instances ont divergé bien au-delà d'un simple réglage isolé.
Toute correction ligne par ligne aurait traité un symptôme sans régler
la cause — la vraie solution serait une resynchronisation complète via
`PROC-001`, un chantier à part entière, non entrepris dans l'urgence de
cette session.

**Décision — Mise à l'arrêt de l'instance production `psm2s_v2`
(03/09/2026, validée par Phil)** : cette instance contenait des données
réelles (créée pour une évaluation par un collègue, Guillaume, qui ne
l'a en pratique jamais utilisée). Compte tenu (1) de données personnelles
réelles en jeu, (2) d'un retard de sécurité substantiel jamais comblé,
(3) d'un usage réel nul, la décision retenue n'est pas de corriger mais
d'**arrêter le service**, plutôt que d'investir dans une resynchronisation
pour un usage qui n'existe plus. Toute décision différente aurait
nécessité de justifier le risque conservé au regard d'un bénéfice
inexistant.
**Exécuté** : archive complète créée (`archive_psm2s_v2_avant_arret_20260903.tar.gz`,
code + base + médias), téléchargée en lieu sûr hors serveur, puis
application arrêtée via cPanel Setup Python App. Vérifié : le site
renvoie une page d'erreur générique, plus aucune donnée accessible.
Rien supprimé — réversible si un besoin réel se présente un jour, en
appliquant `PROC-001` avant toute remise en service.
**Conséquence pour l'audit sécurité en cours** : les constats `DEBUG`,
`ALLOWED_HOSTS` et `SECRET_KEY` avec filet faible concernant `psm2s_v2`
sont neutralisés par l'arrêt du service, pas par une correction — à ne
pas rouvrir sans redéployer proprement au préalable.

**Incohérence relevée avec une décision antérieure** : l'entrée
« Anomalies découvertes lors de la resynchronisation formation »
(05/07/2026, ci-dessus) indique que `DEBUG=True` sur formation avait
déjà été corrigé ce jour-là directement sur le serveur. Or la copie
locale de `config/settings_formation.py` lue le 28/08/2026 pendant
l'audit sécurité montre encore `DEBUG = True` en dur. Ce fichier étant
volontairement **hors Git** (décision L3.1, fichiers spécifiques au
serveur jamais versionnés), la copie locale peut être obsolète par
rapport à l'état réel du serveur — à vérifier en direct avant de
conclure quoi que ce soit, plutôt que de faire confiance à l'un ou
l'autre des deux constats.

---

## Enrichissement tickets démo DEMO-TIL — 10 cas (03/09/2026)

Remplace `extension_quotidien_tilleuls.py` (4 cas, jamais exécuté) par
`enrichissement_tickets_demo_tilleuls.py` (10 cas), suite à une demande
formelle avec cahier des charges détaillé par cas (créateur, responsable,
priorité, prestataire, statut, coût). Même méthode que d'habitude :
inspection en lecture seule d'abord (aucun doublon avec les 3 tickets
réglementaires déjà présents, `AMEB Multiservices` n'existait pas encore),
tableau récapitulatif proposé, arbitrages explicites validés par Phil
(porte coupe-feu → externe AMEB ; stock d'entretien → à traiter sans
intervention ; radiateur → mappé sur « clôturé », `TicketTravaux` n'ayant
pas de statut « réalisé » séparé), puis exécution sur feu vert explicite.

**Exécuté et confirmé le 03/09/2026** : 10 `TicketTravaux`, 8
`Intervention` (aucune pour les cas « à traiter », cohérent avec rien
n'ayant encore été fait), 1 `Prestataire` (AMEB Multiservices) et son
`CorrespondantLocal` créés. Chronologie sur 5 semaines (J-35 à J-1),
6 tickets clôturés, 2 en cours (fuite sanitaire, porte coupe-feu — tous
deux avec une intervention « planifiée » à venir), 2 à traiter (dont un
très récent, J-1). Aucun compte, rôle, permission ni contrôle
réglementaire touché ; les 3 tickets réglementaires déjà présents
inchangés.

**Point technique retenu** : `TicketTravaux.date_creation` et
`Intervention.date_creation` sont en `auto_now_add`, donc ignorés par
`get_or_create()` au moment de la création — le script fixe la date
réelle après coup via une mise à jour ciblée (`.filter(pk=...).update(...)`)
pour obtenir une chronologie crédible plutôt que des dates de création
toutes identiques au jour d'exécution.

**AMEB Multiservices absent du référentiel Partenaires — analyse et
décision (03/09/2026)** : `AMEB Multiservices` n'apparaissait pas dans
`liste_prestataires` car cette vue (et surtout `get_prestataire_ou_404`,
fonction de périmètre/IDOR) n'affichent/n'autorisent un prestataire que
s'il a au moins un `Contrat` visible — `Intervention.prestataire` est un
champ texte libre, jamais lié structurellement à `Prestataire` (choix
délibéré de P4-L3, cf. plus haut). Analyse détaillée fournie : corriger
uniquement l'écran de liste aurait cassé l'accès à la fiche AMEB pour un
rôle Directeur (404, puisque `get_prestataire_ou_404` applique la même
règle comme garde-fou d'accès, pas seulement d'affichage). **Décision de
Phil** : ne pas toucher au code ni aux permissions pour un besoin de
démo — créer à la place un contrat-cadre `CONV-AMEB-2026` (DEMO-TIL,
sans type de contrôle ni montant fixe, notes explicites sur la nature
« maintenance courante »). Exécuté et confirmé le 03/09/2026 (`Contrat`
créé, rien d'autre modifié).

**Question fournisseurs (Leclerc, Bricomarché, etc.) — tranchée pour
l'instant (03/09/2026)** : `Prestataire` n'a aujourd'hui aucun champ de
catégorie/type (vérifié dans `models.py`), contrairement à
`TypeControle`/`Etablissement`. Introduire une distinction
Contrôle/Maintenance/Fourniture serait une vraie évolution fonctionnelle
(champ + migration), pas un ajustement de données. **Décidé** : hors
périmètre de la démo actuelle, à ne considérer que dans le cadre d'une
réflexion produit dédiée sur le périmètre de PSM2S — la base de
démonstration reste volontairement à AMEB + APAVE + SOCOTEC. Principe
retenu par Phil pour la suite : ne jamais ajouter une fonctionnalité
uniquement pour la démonstration — la démo doit refléter ce que PSM2S
sait réellement faire.

**Doublon historique nettoyé au passage (03/09/2026)** : en consultant le
résultat dans l'interface, Phil a repéré deux `Intervention` identiques
sur le ticket réglementaire « Remplacement extincteur hall d'entrée »
(24/07 et 27/07/2026, même montant, même description) — exactement le
type de doublon déjà documenté (clé `get_or_create` construite sur une
date relative, script initial relancé à deux jours différents). Vérifié
en lecture seule puis supprimé (conservé le plus récent, 27/07).
Confirme que ce même défaut, déjà identifié par l'audit du 28/08 et déjà
couvert par `correction_donnees_demo.py` (non exécuté), peut aussi
apparaître ailleurs dans les données DEMO-TIL restées de l'ancien seed —
`correction_donnees_demo.py` reste donc pertinent et à exécuter avant le
tournage plutôt que d'être considéré caduc.

---

## Chantier 1 — Adaptation tablette Android, usage terrain (07/09/2026)

Ouvert après une analyse en lecture seule (`Documentation/02_Architecture/2026-09-07_Reflexion_Tablette_Vocabulaire.md`) ayant confirmé qu'aucune adaptation mobile n'existait dans le code (aucune `@media` dans `base.html`, sidebar fixe 224px, cibles tactiles 26-28px, formulaires en grille 2 colonnes fixe, `TicketTravaux.description` absent de tout formulaire malgré son existence dans le modèle).

**Développé le 07/09/2026, sur le dépôt local (`Code-Source`), non déployé** :
- `Templates/base.html` : sidebar en tiroir sous 900px (bouton menu fixe 44×44, overlay de fermeture, transition CSS), cibles tactiles portées à 44px (`.icon-btn-sm`, `.logout-btn`, `.btn`, `.nav-item`), règle de collapse `.form-row`/`.form-grid` en une colonne — placée délibérément **après** `{% block extra_style %}{% endblock %}` pour ne jamais être écrasée par la redéfinition locale de ces mêmes classes dans chaque template (mécanisme de cascade identifié pendant l'analyse préalable, confirmé fonctionner comme prévu).
- `registre/forms.py` : `TicketTravauxForm` expose désormais `description` (facultatif, `Textarea`) ; `PieceJointeTicketForm` reçoit l'attribut `capture="environment"` sur le champ fichier, sans restriction `accept` — pour ne pas bloquer le dépôt de PDF (devis/factures) via le même champ.
- `Templates/registre/nouveau_ticket.html`, `modifier_ticket.html` : champ description ajouté.
- `Templates/registre/detail_etablissement.html` : bouton « Nouveau ticket » ajouté dans l'en-tête permanent (visible quel que soit l'onglet actif), plus un correctif responsive local — cette page utilise ses propres classes d'en-tête (`.detail-topbar`/`.detail-tabs`), distinctes de `.topbar`, découvertes en cours de développement et donc non couvertes par la règle globale.
- `Templates/registre/tickets.html` : bug trouvé en cours de développement — deux boutons `.icon-btn-sm` avaient une taille imposée en style inline (`22px`), qui aurait rendu la règle globale de 44px inopérante (une règle en ligne l'emporte toujours sur une classe). Corrigé en retirant l'override inline.

**Aucun fichier de vue, de permission ou de modèle touché.** Aucune migration. Aucune donnée de démonstration modifiée.

**Non fait à ce stade, conformément au périmètre** : pas de test navigateur réel exécuté (pas d'accès navigateur/SSH côté assistant pendant ce développement) — vérification visuelle du code uniquement (relecture des fichiers modifiés, cohérence de la cascade CSS). Un test en conditions réelles (largeurs 1280/1024/800/768, tactile, sécurité par rôle) reste à faire par Phil après déploiement sur formation.

**Validation en conditions réelles (07/09/2026)** : tests effectués par Phil sur formation aux 4 largeurs (1280/1024/800/768, navigateur desktop en mode responsive) et sur tablette tactile réelle (Surface Pro 10, en portrait/fenêtre réduite pour déclencher le seuil de 900px) — sidebar en tiroir, bouton menu, création de ticket confirmés fonctionnels. Diff Git relu intégralement par l'assistant et confirmé conforme au périmètre validé (les deux ajustements découverts en cours de développement — `detail_etablissement.html` et `tickets.html` — sont des complétions nécessaires des priorités déjà approuvées, pas un dépassement). Deux fichiers modifiés non liés (`registre/views.py`, correctif signature du 24/08/2026 non commité, et deux fichiers `signatures/*.jpeg`) identifiés dans le diff et confirmés étrangers à ce chantier.

**Extension validée en cours de test réel — pièce jointe à la création du ticket (07/09/2026)** : test réel sur Surface Pro a révélé qu'un technicien ne pouvait pas joindre de photo lors de la création d'un ticket (l'ajout de pièce jointe n'existait que depuis l'écran « Modifier »). Analyse présentée (option minimale : rediriger vers l'ajout de pièce jointe après création ; option retenue : intégrer le champ directement dans « Nouveau ticket »). Implémenté en modification minimale :
- `registre/views.py`, vue `nouveau_ticket` : lecture optionnelle de `request.FILES['piece_jointe_fichier']` après la création du ticket ; si présent, création directe d'un `PieceJointeTicket` (type déduit du `content_type`, `photo` ou `autre`). Le périmètre d'autorisation n'est pas re-vérifié séparément : la pièce jointe est rattachée au ticket qui vient d'être créé dans la même requête, donc déjà filtré par le mécanisme F9 (FORM-PERIMETRE) existant sur le champ `etablissement`.
- `Templates/registre/nouveau_ticket.html` : ajout de `enctype="multipart/form-data"` sur le formulaire et d'un simple champ fichier optionnel (`capture="environment"`, cohérent avec `PieceJointeTicketForm`), sous le champ description.

**Aucun modèle, aucune permission, aucune migration touchés.** La vue `ajouter_piece_jointe` (ajout après coup) et la classe `PieceJointeTicketForm` ne sont pas modifiées — la nouvelle pièce jointe à la création est créée directement (`PieceJointeTicket.objects.create(...)`), sans passer par ce formulaire, pour ne pas altérer son comportement `required` existant.

**Vérification `capture="environment"` en conditions réelles (17/09/2026)** : testé par Phil sur 2 appareils.
- iPhone 11 Pro (Safari) : bascule directement sur l'appareil photo — comportement optimal confirmé.
- Surface Pro 10 (Edge, Windows) : le sélecteur ouvre l'explorateur de fichiers standard, sans raccourci caméra. Confirmé qu'il s'agit d'une limite du navigateur desktop, pas du code : l'attribut `capture` est scopé par le W3C aux navigateurs mobiles, les navigateurs desktop (Chromium/Edge) l'ignorent légitimement. Aucun correctif possible côté application. Sur Windows, le seul chemin reste : prendre la photo via l'app Caméra de Windows, puis la sélectionner comme un fichier classique. Non bloquant pour l'usage cible (tablette tactile mobile) ; assumé comme limite connue pour un usage sur poste Windows.

---

## Phase 5 — Contractualisation, tarification et continuité (ouverte le 17/09/2026)

**P5-L1 — Contractualisation, tarification et périmètre** : analyse de
l'existant et proposition d'architecture fonctionnelle réalisées
(17/09/2026), en lecture seule, aucun développement. Confirmé : aucun
modèle client/organisation n'existe, le modèle `Contrat` désigne
exclusivement les contrats Prestataire (à ne pas confondre avec le futur
contrat commercial PSM2S↔client), aucun mécanisme de tarif/avenant
n'existe. Barème validé transmis par le DT (45/40/35€ selon engagement
24/36/48 mois + maintenance 150€ dégressive). Architecture fonctionnelle
proposée (Client, ContratClient, Avenant, calculs mensuel/annuel séparés)
en attente de validation avant toute architecture technique. **Suspendu**
le jour même au profit de P5-L0 (priorité continuité), non repris depuis.

**P5-L1 — Reprise (19/09/2026)**, après clôture de P5-L0. Analyse
re-vérifiée sur le code actuel et persistée cette fois en document
(`03_Développement/2026-09-19_P5-L1_Analyse_Architecture_Contractualisation.md`
— l'analyse du 17/09 ne l'avait jamais été). Proposition révisée compte
tenu de L3.4.4 (mono-tenant validé) : pas de modèle `Client` séparé
(redondant avec l'instance elle-même), `ContratCommercial` +
`MouvementPerimetre` (noms provisoires) à la place. Dix points listés par
Phil transmis pour arbitrage DT, avec options et recommandation pour
chacun ; deux semblent déjà tranchés (périmètre en cours de contrat,
articulation avec le contrat Prestataire). Toujours en lecture seule,
aucun développement engagé.

**P5-L1 — Arbitrages DT validés (19/09/2026)** : renouvellement =
nouvelle ligne `ContratCommercial` (historique jamais modifié) ; durée
d'engagement modifiable uniquement au renouvellement ; résiliation
anticipée = statut `RESILIE` + date + motif, **aucune règle financière
calculée par le logiciel** (reste des conditions contractuelles) ;
`MouvementPerimetre` validé (type, objet, date d'effet, auteur,
commentaire), un retrait ne supprime jamais l'objet métier ; séparation
stricte actée entre `actif` (état opérationnel) et périmètre contractuel
— **ne jamais automatiser l'un à partir de l'autre** ; 4 statuts
`EN_ATTENTE/ACTIF/RESILIE/EXPIRE` validés, avec réserve technique
explicite : les dates restent la source de vérité, le statut ne doit
jamais s'en écarter silencieusement ; visibilité admin/responsable_securite
uniquement, directeur exclu ; nom `ContratCommercial` validé, aucune
relation avec `Contrat` (Prestataire).

**P5-L1 — Architecture technique détaillée (19/09/2026)**, document
`03_Développement/2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md` :
modèles `ContratCommercial`/`MouvementPerimetre` (champs, contraintes
d'intégrité), fonction pure de reconstruction du périmètre à une date
donnée (jamais dépendante de l'état courant des objets — champs
snapshot + `on_delete=PROTECT`), règles de calcul (tarif mensuel,
maintenance annuelle, signal de dépassement sans blocage, cohérence
statut/dates), impacts vues/formulaires/permissions/tests. Deux points
techniques restent à confirmer avant développement : mouvements de
bâtiment explicites ou implicites à l'entrée d'un établissement dans le
périmètre, et mode de calcul de la date anniversaire de maintenance.
Toujours en conception, aucun code engagé.

**P5-L1 — Point 8 révisé (19/09/2026), pas encore définitivement clos.**
Principe modifié : « consultation élargie, modification restreinte » —
le directeur peut désormais **consulter** les informations commerciales
de son instance (durée, dates, statut, tarif, maintenance), mais ne peut
rien modifier (réservé admin/responsable_securite, inchangé). Sous-point
explicitement laissé ouvert par Phil : la portée exacte de cette
consultation pour un directeur rattaché à un seul établissement, quand le
contrat couvre plusieurs établissements — les champs globaux du contrat
(tarifs unitaires, dates, statut) ne posent pas de problème (identiques
pour tous), mais les agrégats sur l'ensemble du périmètre (nombre total
d'établissements/bâtiments, montant mensuel total) révèlent la taille de
l'organisation au-delà de son propre site. Deux options documentées dans
`2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md` §4.1,
recommandation pour une vue scopée par établissement
(`_get_etab_ids_autorises`) plutôt que l'agrégat global. Décision finale
à confirmer par Phil.

**P5-L1 — Point 8, deuxième révision (19/09/2026) : habilitation
contractuelle, indépendante du `role`.** Constat de Phil : le droit de
*gérer* le contrat commercial ne doit pas dépendre uniquement du `role`
— un utilisateur (typiquement un directeur) peut être le
souscripteur/gestionnaire réel du contrat. Proposition documentée
(§4.2 du document d'architecture technique) : champ
`ContratCommercial.gestionnaire_contractuel` (FK vers `Utilisateur`,
assignable uniquement par admin/responsable_securite, pré-rempli au
renouvellement depuis le contrat précédent, modifiable). Droits de
gestion accordés soit par le rôle (admin/responsable_securite,
toujours), soit par cette désignation explicite sur le contrat actif —
vérifié par une fonction dédiée résolue contre l'objet, jamais contre le
seul rôle (même discipline IDOR que le reste de PSM2S). Décision à
confirmer par Phil avant développement.

**P5-L1 — Point 8 tranché définitivement (19/09/2026).** Un seul
`gestionnaire_contractuel` par `ContratCommercial` (pas de liste — DT
tranché explicitement, simplicité et lisibilité juridique). Assignable
uniquement par admin/responsable_securite. Renouvellement : gestionnaire
précédent pré-rempli, validation explicite obligatoire, jamais de
reconduction silencieuse. Chaque `ContratCommercial` historique garde sa
propre référence (historique interprétable même si le gestionnaire
change à chaque renouvellement). Nouveau point ajouté par Phil : si le
gestionnaire désigné quitte ou est désactivé en cours de contrat, **le
contrat reste valide, aucune révocation automatique** — un signal
« Le contrat n'a plus de gestionnaire contractuel actif » s'affiche pour
admin/responsable_securite, qui peuvent désigner un remplaçant à tout
moment. Matrice finale de permissions et détail complet dans
`2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md`.

**P5-L1 — Les 10 arbitrages fonctionnels sont considérés comme
suffisamment définis (19/09/2026, Phil).** Étape suivante engagée :
architecture technique détaillée de `ContratCommercial` et
`MouvementPerimetre` (document ci-dessus), toujours en conception, aucun
code engagé. Deux points techniques restent ouverts avant développement :
mouvements de bâtiment explicites ou implicites, et mode de calcul de la
date anniversaire de maintenance.

**P5-L1 — Interaction création établissement / périmètre contractuel
(19/09/2026, question de Phil).** `nouveau_etablissement` (vue
existante, `@gestionnaire_requis` — accessible aussi au directeur) reste
inchangée dans son périmètre technique, mais affichera désormais un
message informatif signalant que l'établissement n'est pas encore dans
le périmètre contractuel, avec un raccourci de création du mouvement de
périmètre réservé aux utilisateurs habilités (admin/responsable_securite/
gestionnaire_contractuel). **Aucune pré-validation bloquante** — cohérent
avec la règle « jamais de blocage, toujours un signal » déjà retenue
partout ailleurs dans ce lot. Détail dans
`2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md` §4.4.

**Révisée le 19/09/2026, voir entrée suivante** — le « raccourci de
création du mouvement de périmètre » ci-dessus est remplacé par un
workflow de demande (`DemandeAvenant`). Entrée conservée pour
l'historique, ne plus s'y référer pour l'implémentation.

**P5-L1 — Introduction de `DemandeAvenant` (19/09/2026), révise le point 5
et le §4.4 ci-dessus.** Proposition initialement soumise par Phil à
partir d'une réflexion de ChatGPT, discutée avec l'assistant, puis
validée par Phil avec ajustements. Décisions actées :

- Un troisième objet, `DemandeAvenant`, s'intercale entre la
  constatation d'un changement de périmètre (ex. création d'un
  établissement) et son application effective. `ContratCommercial`
  reste l'objet du contrat ; `DemandeAvenant` devient l'objet de
  workflow ; `MouvementPerimetre` reste exclusivement la source de
  vérité des changements effectivement appliqués — **jamais transformé
  en objet hybride** (raison explicite du choix d'un objet séparé
  plutôt que d'un statut ajouté à `MouvementPerimetre`).
- Toute modification de périmètre passe obligatoirement par une
  `DemandeAvenant`. Une demande validée génère les `MouvementPerimetre`
  correspondants (un par établissement/bâtiment concerné). Une demande
  rejetée ne modifie jamais le périmètre et n'est jamais lue par le
  calcul de périmètre.
- **Trois statuts seulement** : `EN_ATTENTE`, `VALIDEE`, `REJETEE` — pas
  de `DEMANDE`/`A_VALIDER` distincts, pas de `APPLIQUEE` (la présence
  des `MouvementPerimetre` liés en est la preuve).
- **Qui fait quoi** : créer un établissement et déclencher une
  `DemandeAvenant` suivent le même droit (celui de
  `nouveau_etablissement` : admin/responsable_securite/directeur) ;
  valider ou rejeter reste réservé à admin/responsable_securite/
  gestionnaire_contractuel ; **personne, aucune interface, ne peut
  créer un `MouvementPerimetre` directement** — précision formelle du
  point 5 initial.
- **Aucun raccourci, même pour les rôles habilités** : un
  admin/responsable_securite/gestionnaire_contractuel qui ajoute
  lui-même un établissement passe par le même mécanisme (créer la
  demande puis la valider dans le même parcours) — pour que l'audit
  reste uniforme quel que soit qui agit.
- **Écran d'impact chiffré**, affiché à la soumission et à la
  validation (établissements/bâtiments avant→après, abonnement mensuel
  avant→après, rappel 1er du mois suivant / pas de prorata) — la trace
  de décision est portée par les champs `validateur`/`date_traitement`
  de `DemandeAvenant`, pas par un champ de confirmation séparé.
- **Pas de système de notifications pour P5-L1** (décision explicite,
  pour ne pas gonfler le lot) — une liste des demandes en attente,
  visible dans l'interface, suffit fonctionnellement. Notification
  interne, email, rappels : candidats pour un lot ultérieur.

Détail complet (modèles `DemandeAvenant`/`LigneDemandeAvenant`, écrans,
permissions, tests) dans
`2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md` §1.3 et
§4.4 (révisés), et dans
`2026-09-19_P5-L1_Analyse_Architecture_Contractualisation.md` (D bis et
révision du point 5). Toujours en conception, aucun code engagé.
Prochaine étape annoncée par Phil : revue de l'architecture technique de
`DemandeAvenant` avant d'autoriser le développement.

**P5-L0 — Continuité, sécurité et pérennité du projet** : audit complet
en lecture seule (17/09/2026), puis repassage de contrôle (19/09/2026,
aucun changement constaté entre les deux), puis clôture actée le
19/09/2026 avec les actions suivantes :

- **Git** : commit et push confirmés par Phil sur les deux dépôts GitHub
  (l'assistant n'ayant pas d'accès shell fonctionnel durant cette
  session) : `psm2s-securite` (chantier tablette + ajout pièce jointe à
  la création, commit `d0051ef`) et `psm2s-documentation` (mises à jour
  documentaires du jour, 49 fichiers, commit `3cb98d2`). Arbres propres
  confirmés sur les deux dépôts à ce stade.
- **Secrets** : vérifié qu'aucun code ne dépend de `Cle.txt` ni de
  `la derniere clé secret_key.txt` (seules des mentions historiques dans
  la documentation/scripts d'audit). Le mécanisme officiel
  (`DJANGO_SECRET_KEY` en variable d'environnement, `get_env_required`,
  sans valeur de secours) reste inchangé et confirmé comme seule source
  active. Suppression des deux fichiers actée, à exécuter par Phil
  (hors accès fichier de l'assistant).
- **Formation — DEBUG** : `config/settings_formation.py` codait
  `DEBUG = True` en dur, en violation du défaut sûr de `settings.py`
  (anomalie déjà documentée dans `PROC-001` §Étape 0.2, réapparue).
  Corrigé : la ligne est retirée, formation hérite désormais du même
  comportement que tout le reste (`DEBUG=False` sauf `DJANGO_DEBUG=True`
  explicite en environnement). Le développement local n'est pas affecté
  (variable posée dans le shell local, jamais dans le fichier de config).
  Vérification par `manage.py check --deploy` sous
  `DJANGO_SETTINGS_MODULE=config.settings_formation` à faire par Phil
  après déploiement du correctif sur le serveur.
- **Documentation** : `POINT_DE_REPRISE.md` réécrit (état à jour,
  redirige explicitement vers `INDEX.md` comme point d'entrée officiel,
  au lieu de se présenter lui-même comme tel). `INDEX.md` mis à jour
  (état actuel, `PROC-003` référencée, correction de la mention erronée
  sur la disparition du dossier `Audits/`, note sur la suppression actée
  des secrets locaux). Aucune nouvelle architecture documentaire créée.
- **Hygiène** : suppression actée de deux fichiers étrangers au projet
  dans `Documentation/04_Juridique/` (`ChatGPT Installer.exe`,
  `Microsoft.Services.Store.winmd`) — à exécuter par Phil.
- **Restauration** : `PROC-003_Restauration_PSM2S.docx` (déjà rédigée par
  Phil) prise en compte et référencée dans `INDEX.md`. Aucun nouveau
  système de sauvegarde créé — mécanismes existants documentés tels
  quels (sauvegarde BDD côté serveur, JetBackup, copie ponctuelle
  externe).
- **Crash-test de reprise (19/09/2026)** : **crash-test validé sur
  l'instance PSM2S Formation** — restauration sur un nouveau poste,
  démarrage de l'application et validation fonctionnelle approfondie par
  Phil réussis. Le test valide la procédure de reprise
  (`PROC-003_Restauration_PSM2S.docx`) d'une instance PSM2S complète sur
  un nouvel environnement — validation pratique concrète de la capacité
  de reprise du projet. Le test n'a pas porté sur toutes les
  configurations possibles de clients futurs.
- **Core/Variantes (L3.4.4)** : statut fait évoluer de « proposition en
  attente » à **« VALIDÉE COMME ORIENTATION ARCHITECTURALE —
  IMPLÉMENTATION DIFFÉRÉE »**. Aucun développement réalisé dans P5-L0 sur
  ce sujet — décision d'orientation actée uniquement, cohérente avec
  `POLITIQUE-001`.

### Sécurité — anciennes clés présentes dans des fichiers historiques (19/09/2026)

Lors de la revue de continuité P5-L0, deux fichiers historiques
(`passenger_wsgi.py` et `passenger_wsgi_ORIGINAL.py`) contenaient
d'anciennes valeurs de `SECRET_KEY` provenant de l'ancienne instance de
production `psm2s_v2`.

Vérification effectuée le 19/09/2026 (comparaison d'empreintes SHA-256,
sans jamais afficher ni comparer de valeur en clair) : ces valeurs ne
correspondent pas à la clé actuellement utilisée par l'instance
Formation. L'ancienne instance de production `psm2s_v2` ayant été
décommissionnée le 03/09/2026, aucune clé active de cette instance n'est
actuellement en service.

**Décision :**
- retirer ces deux fichiers de l'état suivi du dépôt (`git rm --cached`,
  chemins ajoutés au `.gitignore`) ;
- conserver les fichiers dans l'archive historique locale (ancien PC)
  pour préserver la traçabilité ;
- ne pas réécrire l'historique Git à ce stade ;
- considérer les anciennes clés comme révoquées et non utilisables ;
- aucune valeur de clé ni empreinte n'est inscrite dans cette
  documentation.

### Sécurité — jeton d'accès GitHub exposé, révoqué (19/09/2026)

Lors du même scan de sécurité, un fichier `Jeton généré pour l'API Github
le 05-06-2026.txt` (format de jeton personnel GitHub réel) a été repéré à
la racine du dépôt `Code-Source`. Vérification par
`git log --all --full-history` : le fichier a été suivi et poussé sur
GitHub via deux commits de juin 2026 (`1f5cd811`, `69d63342`). Une copie
identique existe également dans l'archive historique
`archive_psm2s_v2_avant_arret_20260903.tar.gz` (dépôt
`psm2s-documentation`), provenant de la même origine (ancienne production
`psm2s_v2`) — inspection de la liste des fichiers de l'archive
uniquement, aucun contenu extrait ni affiché.

**Révocation confirmée par Phil le 19/09/2026** (GitHub, Developer
settings → Personal access tokens). Aucun nouveau jeton généré, l'accès
n'étant plus utilisé pour ce projet.

**Décision :**
- retirer le fichier `Jeton généré pour l'API Github le 05-06-2026.txt`
  du suivi Git du dépôt `Code-Source` (`git rm --cached`), chemin ajouté
  au `.gitignore` du dépôt ;
- conserver le fichier sur l'ancien PC (aucune suppression physique) ;
- conserver telle quelle la copie présente dans l'archive
  `archive_psm2s_v2_avant_arret_20260903.tar.gz` — une archive historique
  de production est censée contenir l'état réel de l'époque ; la
  révocation du jeton neutralise le risque indépendamment de sa présence
  dans une sauvegarde ;
- ne pas réécrire l'historique Git à ce stade ;
- aucune valeur de jeton n'est inscrite dans cette documentation.

## Clôture formelle — P5-L0 (19/09/2026)

Toutes les actions de clôture (Git, secrets, Formation, documentation,
hygiène, restauration, crash-test, Core/Variantes) et le volet sécurité
complémentaire (anciennes clés `passenger_wsgi*`, jeton GitHub) sont
désormais exécutés et vérifiés :

- **Jeton GitHub** : révocation confirmée par Phil le 19/09/2026.
- **Retrait du suivi Git** : fichier du jeton retiré de `Code-Source`
  (commit `5b41ed6`, poussé) ; les deux fichiers `passenger_wsgi*`
  retirés de `Documentation` (commit `d590cd0`, poussé), complété par un
  commit de finalisation du `.gitignore` (commit `9fa3b22`, poussé).
- **Arbres Git propres, confirmés sur les deux dépôts** :
  `psm2s-securite` à `5b41ed6`, `psm2s-documentation` à `9fa3b22`.
- **Correctif `DEBUG=False` de `settings_formation.py`** : vérifié
  **effectivement déployé sur le serveur Formation** (pas seulement dans
  le dépôt) — `manage.py check --deploy` sous
  `DJANGO_SETTINGS_MODULE=config.settings_formation` ne signale plus
  `security.W018`. Les 4 avertissements restants (W004 HSTS, W008 SSL
  redirect, W012/W016 cookies sécurisés) sont le chantier déjà connu et
  volontairement reporté **L3.1a — Durcissement HTTPS formation**
  (04/07/2026), hors périmètre de P5-L0. Site Formation confirmé
  accessible et fonctionnel après vérification.

**P5-L0 est déclaré formellement clos le 19/09/2026.**

---

*Fichier vivant : ajouter une entrée par décision structurante validée en
revue, sous la phase correspondante. Ne pas y consigner de décision non
actée.*
