# P5-L1 — Bilan complet (audit du 24/09/2026)

Document d'audit, produit sur GO explicite de Phil, après clôture des lots
A, B, C0, C1, C2, C3 et C4. Aucun code modifié pour produire ce document.
Chaque affirmation ci-dessous a été vérifiée directement dans le code
(`registre/models.py`, `permissions.py`, `contractualisation.py`,
`forms.py`, `views.py`, `urls.py`, `Templates/registre/commercial/`,
`registre/tests.py`) et dans les migrations réellement présentes dans le
dépôt — aucune décision de `DECISIONS.md` ou des documents d'analyse/
proposition n'a été supposée correctement implémentée sans vérification.

---

## 1. État fonctionnel réel de P5-L1

Le parcours complet est fonctionnel de bout en bout, sur le dépôt tel que
poussé (commit `b755ad1`, `main` à jour) :

**Contrat** : création (`renouvellement_form`, toujours `EN_ATTENTE`) →
activation (`activer_contrat`, bascule atomique avec l'ancien contrat) →
consultation (`contrat_detail`, `commercial_accueil`) → renouvellement
(nouveau `renouvellement_form` avec reprise de périmètre) → résiliation
(`resiliation_form`, réservée au contrat `ACTIF`) → historique
(`contrat_historique`, chaîné via `contrat_precedent`).

**Périmètre** : demande d'ajout/retrait (`demande_avenant_form`, étape 1)
→ prévisualisation de l'impact (même vue, étape 2, aucune écriture) →
confirmation explicite → `EN_ATTENTE` → validation ou rejet
(`demande_avenant_valider`/`demande_avenant_rejeter`) → création des
`MouvementPerimetre` (validation uniquement) → nouveau périmètre
opérationnel immédiatement reflété par `perimetre_a_date`.

Le principe central — **le logiciel ne modifie jamais silencieusement le
périmètre contractuel** — est respecté à chaque point de vérification :
aucune vue ne crée de `MouvementPerimetre` en dehors de
`demande_avenant_valider` (et de l'auto-validation explicite de
`renouvellement_form`, qui reste un geste utilisateur unique et tracé,
jamais un automatisme caché) ; chaque `MouvementPerimetre` porte
obligatoirement une `ligne_demande_origine` (contrainte structurelle,
`OneToOneField` non nul) ; chaque écran d'écriture (activation,
soumission, validation, rejet) affiche ses effets avant de les appliquer
et n'écrit que sur une confirmation explicite distincte de l'affichage.

## 2. État technique réel

Code cohérent avec les arbitrages documentés, à deux réserves de
concurrence près (détaillées en §8) et une fonctionnalité de l'architecture
initiale jamais construite (détaillée en §10). Aucune dette de structure :
un seul point d'entrée pour chaque règle métier (`contractualisation.py`
pour les calculs, `permissions.py` pour les autorisations), pas de
duplication de logique entre les vues.

## 3. Modèles, relations et migrations

Une seule migration pour tout P5-L1 :
`0024_contratcommercial_demandeavenant_lignedemandeavenant_and_more.py`
(Lot A). Aucune migration ajoutée en B, C0, C1, C2, C3 ou C4 — cohérent
avec l'engagement pris à chaque lot de ne toucher aux modèles que si
techniquement nécessaire et signalé au préalable ; aucun cas ne s'est
présenté après le Lot A.

Les quatre modèles (`ContratCommercial`, `DemandeAvenant`,
`LigneDemandeAvenant`, `MouvementPerimetre`) correspondent exactement à
ce que documentent l'architecture technique et `DECISIONS.md` :
`full_clean()` appelé dans chaque `save()`, `OneToOneField`
`MouvementPerimetre.ligne_demande_origine` non nul avec `on_delete=PROTECT`,
snapshot (`nom_historique`/`etablissement_code_historique`) pris à la
sauvegarde si absent, règle « 1er du mois » appliquée de façon identique
sur `date_debut`, `date_effet_souhaitee` et `date_effet`. La contrainte
« un seul contrat `ACTIF` » (mono-tenant, cf. §7) reste strictement
applicative (`ContratCommercial.clean()`), jamais portée par la base —
conforme à la décision du Lot A.

## 4. Matrice effective des permissions

Vérifiée directement dans `permissions.py` et le décorateur de chaque vue :

| Vue | Décorateur | Contrôle objet |
|---|---|---|
| `commercial_accueil`, `contrat_detail`, `contrat_historique` | `@gestionnaire_requis` | `gestion_contrat_autorisee` (agrégats) / `verifier_acces_gestion_contrat` (historique) |
| `renouvellement_form`, `activer_contrat` | `@commercial_gestion_requis` | aucun (admin/responsable_securite seuls, action non liée à un contrat déjà résolu) |
| `resiliation_form`, `demande_avenant_valider` | `@gestionnaire_requis` | `verifier_acces_gestion_contrat` |
| `demande_avenant_form`, `demande_avenant_liste` | `@gestionnaire_requis` | `demandes_avenant_visibles` / périmètre serveur (`etablissements_autorises`) |
| `demande_avenant_rejeter` | `@gestionnaire_requis` | `verifier_acces_gestion_contrat` |

La distinction `commercial_gestion_requis` (rôle seul, admin/responsable
uniquement, même le gestionnaire_contractuel directeur est refusé) contre
`gestionnaire_requis` + `verifier_acces_gestion_contrat` (rôle large,
mais le gestionnaire désigné passe sur son contrat) est appliquée
exactement comme documentée dans l'arbitrage n°1 du Lot C4 et la
proposition technique C2 §1 — testée explicitement
(`test_refuse_directeur_meme_gestionnaire` sur `activer_contrat`,
`test_gestionnaire_du_contrat_autorise` sur `resiliation_form`).

Point de vigilance mineur (non bloquant) : les docstrings de
`gestion_contrat_autorisee`, `verifier_acces_gestion_contrat` et
`demandes_avenant_visibles` dans `permissions.py` affirment encore
« Aucune vue de ce lot n'appelle encore ces fonctions (Lots C/D) » — vrai
au moment de leur écriture (Lot B), obsolète depuis C1/C2/C4 qui les
appellent toutes. Aucun impact fonctionnel, uniquement un commentaire à
rafraîchir.

## 5. Parcours complet ContratCommercial

Vérifié vue par vue (`views.py`, lignes 3247-3570) :

- `renouvellement_form` crée toujours `EN_ATTENTE`, `contrat_precedent`
  forcé par la vue (jamais exposé au formulaire), périmètre pré-coché
  depuis l'ancien contrat mais rien écrit avant soumission.
- `activer_contrat` : écran de confirmation nommant les deux effets
  (bascule ancien → `EXPIRE`, nouveau → `ACTIF`) avant toute écriture ;
  transaction verrouillée (`select_for_update` sur les deux contrats),
  états re-vérifiés après verrouillage, refus propre si le contrat visé
  n'est plus `EN_ATTENTE` ou si l'ancien n'a pas atteint sa `date_fin`.
- `resiliation_form` : réservée au contrat `ACTIF`, quel que soit le
  `pk` passé dans l'URL.
- `contrat_historique` : chaîne remontée via `contrat_precedent`,
  redirection vers `commercial_accueil` en l'absence de tout contrat.

## 6. Parcours complet DemandeAvenant → MouvementPerimetre

Vérifié vue par vue (`views.py`, lignes 3591-3975) :

- `demande_avenant_form` : sélection (GET) → prévisualisation (POST sans
  `confirme`) → confirmation (POST avec `confirme=1`) — aucune écriture
  avant confirmation explicite. Contrôle serveur du périmètre candidat
  (indépendant de l'affichage), anti-doublon par objet touché (pas par
  état coché inchangé), date d'effet contrôlée (1er du mois, pas
  antérieure au mois suivant).
- `demande_avenant_valider` : écran de confirmation sans écriture (GET),
  transaction verrouillant `DemandeAvenant` **et** `ContratCommercial`
  (`select_for_update` sur les deux), états re-vérifiés après
  verrouillage, refus propre sans écriture si le contrat n'est plus
  `ACTIF`, un `MouvementPerimetre` créé par ligne avec
  `ligne_demande_origine` renseignée.
- `demande_avenant_rejeter` : transaction verrouillant uniquement
  `DemandeAvenant`, motif obligatoire (`DemandeAvenantRejetForm`), reste
  possible même si le contrat n'est plus `ACTIF`.

Les 8 arbitrages du 24/09/2026 (6 initiaux + 2 complémentaires) sont
implémentés exactement comme tranchés, sans écart constaté.

## 7. Protections IDOR

Deux familles cohabitent dans le code, confirmées par grep exhaustif sur
`views.py` : la famille établissement/prestataire (`Http404`, en dehors
du périmètre P5-L1) et la famille contractuelle
(`verifier_acces_gestion_contrat`, refus par redirection vers le
dashboard). **Aucune occurrence de `Http404` dans tout le bloc
commercial** (lignes 3230-3975) — la famille redirection est utilisée de
façon strictement homogène sur les 5 vues d'écriture/consultation
protégée. Testé explicitement côté GET et POST forcé
(`test_idor_directeur_hors_perimetre_refuse_meme_par_post_force`).

## 8. Transactions, verrouillages et garanties de rollback

Cinq points d'écriture identifiés, tous en `transaction.atomic()` :
`renouvellement_form`, `activer_contrat`, `demande_avenant_form`,
`demande_avenant_valider`, `demande_avenant_rejeter`. Verrouillage
(`select_for_update`) présent exactement là où les arbitrages le
prévoient : `activer_contrat` (les deux contrats), `demande_avenant_valider`
(demande + contrat), `demande_avenant_rejeter` (demande seule).

**Le cœur fonctionnel de C4 est bien couvert** :
`test_rollback_complet_si_echec_en_cours_de_transaction` (sur
`DemandeAvenantValiderTests` comme sur `ActiverContratTests`, même
patron) simule un échec en cours de transaction et vérifie que l'objet
concerné et le périmètre restent dans leur état antérieur — aucun état
intermédiaire persisté.

Deux réserves de concurrence, non testées et non couvertes par un
verrouillage, à signaler comme dette technique (aucune n'a été identifiée
comme un point d'arbitrage explicite dans les lots précédents, donc
aucune n'est un écart par rapport à une décision actée — ce sont des
angles morts, pas des régressions) :

- `demande_avenant_form` : le contrôle anti-doublon (recouvrement
  établissement/bâtiment sur les demandes `EN_ATTENTE`) est exécuté
  **avant** l'ouverture de la transaction d'écriture, sans verrouillage.
  Deux soumissions concurrentes sur le même établissement pourraient
  toutes deux passer le contrôle avant qu'aucune n'ait encore écrit,
  produisant deux `DemandeAvenant` `EN_ATTENTE` qui se chevauchent — ce
  que l'invariant « au plus une demande `EN_ATTENTE` par objet » est
  censé exclure structurellement. La proposition technique C4 §7
  s'appuie explicitement sur cet invariant pour justifier l'absence de
  protection supplémentaire contre la double validation ; la fenêtre de
  course identifiée ici en est donc la seule brèche potentielle connue.
  Risque pratique faible (action réservée aux gestionnaires, usage
  interne, pas d'automatisation susceptible de soumettre deux requêtes
  simultanées), mais réel en théorie.
- `renouvellement_form` : la lecture du contrat `ACTIF` courant
  (`ancien`) se fait avant la transaction, sans verrouillage. Deux
  renouvellements concurrents pourraient produire deux contrats
  `EN_ATTENTE` référençant le même `contrat_precedent`. Sans conséquence
  sur l'intégrité du périmètre (seule `activer_contrat`, correctement
  verrouillée, peut faire passer un contrat à `ACTIF`), mais peut
  produire un doublon de contrat `EN_ATTENTE` à nettoyer manuellement.

## 9. Tests : nombre, répartition, cas protégés

364 tests au total dans `registre/tests.py`, tous verts (confirmé par la
dernière exécution complète sur Formation, 364/364 OK, 3 skips SQLite
`select_for_update` connus et justifiés). Répartition P5-L1 (169 tests,
recomptée précisément ligne par ligne pour ce bilan) :

| Lot | Tests |
|---|---|
| A — modèles | 30 |
| B — permissions | 20 |
| C0 — calculs (`contractualisation.py`) | 20 |
| C1 — consultation | 14 |
| C2 — renouvellement/activation/résiliation | 31 |
| C3 — soumission/liste des demandes | 28 |
| C4 — validation/rejet | 26 |
| **Total P5-L1** | **169** |

Cas sensibles couverts et vérifiés dans le code des tests eux-mêmes (pas
seulement dans leur nom) : rollback transactionnel complet (C2 et C4),
IDOR par POST forgé, doublons de demandes `EN_ATTENTE`, permissions
croisées entre contrats (« être gestionnaire d'un contrat ne donne aucun
droit sur un autre »), désactivation d'un gestionnaire en cours de
contrat, historique conservé après résiliation/rejet, snapshot
indépendant de l'état courant de l'objet.

## 10. Écarts entre `DECISIONS.md`, les documents P5-L1 et le code

Deux écarts réels identifiés :

1. **Signal « gestionnaire contractuel actif » jamais implémenté.**
   L'architecture technique du 19/09/2026 (§4.2/§4.3, reprise dans
   `DECISIONS.md` ligne 992-995) décrit explicitement un signal
   « Le contrat n'a plus de gestionnaire contractuel actif », affiché à
   admin/responsable_securite quand le gestionnaire désigné est
   désactivé. La proposition technique du Lot C1 (qui a implémenté la
   consultation et le seul signal `statut_coherent`) ne mentionne plus ce
   second signal — sans qu'aucune décision explicite de `DECISIONS.md` ne
   le descope. Le code confirme l'absence totale : aucune occurrence dans
   `contractualisation.py` ni dans aucun template
   `Templates/registre/commercial/`. Fonctionnellement mineur (le champ
   `gestionnaire_contractuel` reste visible en fiche, et
   `gestion_contrat_autorisee` vérifie déjà `is_active` avant d'accorder
   un droit — la désactivation n'ouvre donc aucune brèche de sécurité),
   mais c'est un engagement documenté jamais tenu, glissé entre deux lots
   sans trace de décision.
2. **Corrigé pendant ce bilan** : l'entrée de clôture C3 que j'ai
   ajoutée moi-même à `DECISIONS.md` la semaine dernière indiquait
   « 30 tests dédiés ». Le compte exact, revérifié ligne par ligne pour
   ce bilan, est **28** (`DemandeAvenantSansContratActifTests` 2 +
   `DemandeAvenantFormTests` 10 + `DemandeAvenantPermissionsTests` 7 +
   `DemandeAvenantDoublonsTests` 3 + `DemandeAvenantListeTests` 6). Écart
   mineur, sans conséquence fonctionnelle, mais qui illustre exactement
   le risque que ce bilan cherche à couvrir : une divergence peut
   s'introduire dans la documentation même quand le code est correct. Je
   ne l'ai pas corrigé dans `DECISIONS.md` (aucune modification hors de
   ce document, comme demandé) — à corriger sur votre validation.

Aucun autre écart constaté : les 8 arbitrages C4, les 8 arbitrages C3
(4+4 selon regroupement), les arbitrages C2 (Option A, séquence
renouvellement) et le point 8 du kick-off (gestionnaire_contractuel
unique, non révocable automatiquement) sont tous implémentés exactement
comme documentés.

## 11. Dettes techniques et points de vigilance ouverts

- Les deux fenêtres de concurrence sans verrouillage (§8) —
  `demande_avenant_form` et `renouvellement_form`.
- Le signal « gestionnaire contractuel actif » non implémenté (§10),
  documenté mais abandonné en route.
- Les docstrings obsolètes de `permissions.py` (§4) — cosmétique, aucun
  impact fonctionnel.
- Le mécanisme `MODULES_ACTIFS` (L3.4.4, Phase 4) ne couvre pas le
  module commercial — vérifié comme volontaire (son propre commentaire
  de code limite son premier lot d'implémentation à Eau/Commissions/
  DUERP/Accessibilité) et non comme un oubli, mais à garder en tête si
  une future instance PSM2S ne devait pas exposer la contractualisation.
- Aucune dette structurelle sur les modèles, migrations ou le principe
  mono-tenant (§ suivant) — rien à signaler de ce côté.

## 12. Cohérence avec L3.4.4 (mono-tenant) et éléments avant industrialisation

Le principe mono-tenant (« l'instance elle-même est le client, un seul
contrat commercial vivant possible ») est respecté à tous les niveaux
vérifiés : contrainte applicative dans `ContratCommercial.clean()`,
jamais de logique multi-contrats simultanés dans aucune vue, le
mécanisme `MODULES_ACTIFS` de L3.4.4 (permettant à une instance de ne pas
activer certains modules métier) reste indépendant de la
contractualisation et n'a jamais eu vocation à la couvrir dans son
premier lot d'implémentation.

Avant de considérer P5-L1 comme définitivement industrialisé, les
éléments suivants restent à votre arbitrage (aucun n'est bloquant pour
l'usage actuel sur Formation) :

- Décider si le signal « gestionnaire contractuel actif » doit encore
  être développé (dette documentée en §10) ou être formellement abandonné
  dans `DECISIONS.md`.
- Décider si les deux fenêtres de concurrence du §8 justifient un
  verrouillage supplémentaire, ou si le risque pratique (rôles restreints,
  usage interne non automatisé) est jugé acceptable tel quel.
- Corriger le chiffre « 30 tests dédiés » en « 28 » dans l'entrée de
  clôture C3 de `DECISIONS.md` (écart mineur signalé en §10, point 2).
- Rafraîchir les docstrings obsolètes de `permissions.py` (§4), à traiter
  en même temps qu'un futur lot touchant ce fichier plutôt qu'en isolé.

Aucun de ces quatre points n'appelle un développement urgent : le
workflow contractuel est fonctionnellement complet, testé et cohérent
avec les décisions actées. Ce sont des affinages, pas des correctifs.
