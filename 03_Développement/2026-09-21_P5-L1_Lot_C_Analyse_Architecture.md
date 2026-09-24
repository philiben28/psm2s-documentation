# P5-L1 — Lot C : analyse d'architecture (vues/fonctionnalités de contractualisation)

Document d'analyse, préalable à toute proposition technique et à tout
développement. **Aucune modification de code.** Fait suite au Lot B
(commit `31a0fdf`, 245/245 tests verts, permissions en place).

Méthode suivie : lecture du code réellement présent après le Lot B
(modèles, permissions, `urls.py`, `forms.py`, vues et templates
existants), confrontée aux 6 fonctionnalités demandées et à
l'architecture technique déjà validée
(`2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md`).

---

## 1. État du code après le Lot B (vérifié)

- **Modèles** (`registre/models.py`, lignes 1522-1854, Lot A) :
  `ContratCommercial`, `DemandeAvenant`, `LigneDemandeAvenant`,
  `MouvementPerimetre` — complets, aucun changement depuis.
- **Permissions** (`registre/permissions.py`, Lot B, commit `31a0fdf`) :
  `commercial_gestion_requis`, `gestion_contrat_autorisee`,
  `verifier_acces_gestion_contrat` (patron **redirection**),
  `demandes_avenant_visibles`. Toutes testées (20 tests dédiés),
  **aucune vue ne les appelle encore**.
- **`registre/urls.py`** (178 lignes, lu intégralement) : aucune route
  `commercial*`/`contrat_commercial*`/`demande_avenant*` n'existe. En
  revanche, des routes `contrat` existent déjà pour un objet
  **différent** : `nouveau_contrat`/`modifier_contrat`/`supprimer_contrat`
  (lignes 130-132) portent sur le modèle `Contrat` (contrat avec un
  **Prestataire** externe — Phase 4), pas sur `ContratCommercial`. Les
  deux objets coexistent dans la même application. **Point de vigilance
  signalé au §5** : le nom court « contrat » est déjà pris.
- **`registre/forms.py`** (768 lignes, lu intégralement) : aucun
  `ContratCommercialForm`/`DemandeAvenantForm` n'existe. Convention
  constante sur tous les formulaires existants : `ModelForm`, `widgets`
  avec classes `form-input`/`form-select`, dict `labels`, `__init__`
  surchargé pour rendre certains champs optionnels et filtrer les
  querysets par périmètre (`etablissements_autorises`) ou par contexte
  (`etab_pk`), parfois `save()` surchargé pour une logique de
  résolution/dédoublonnage (`ContratForm.save()`,
  `PrestataireForm.save()` — précédents directs pour un formulaire qui
  fait plus qu'un simple mapping champ-à-champ).
- **`registre/views.py`** : aucune vue `ContratCommercial`/
  `DemandeAvenant` n'existe (confirmé au Lot B, toujours vrai).
  Conventions systématiques relevées sur les vues comparables
  (`nouveau_contrat`/`modifier_contrat`/`supprimer_contrat`, lignes
  1834-1883 ; `liste_prestataires`/`detail_prestataire`/
  `nouveau_prestataire`, lignes 1898-2029) : décorateur de permission en
  tête, résolution de l'objet via un helper `get_*_ou_404`, POST/GET
  classique (pas de `class-based view`), `redirect('registre:...')`
  après un POST valide, `render` avec un contexte simple. `messages`
  (`django.contrib.messages`) utilisé pour les confirmations/erreurs
  ponctuelles (`duerp_signer`, `droits_signature_liste`) — jamais pour
  une redirection de permission (qui reste silencieuse, cf. Lot B).
- **Aucun précédent de vue « valider/rejeter »** dans toute
  l'application (recherche ciblée) : le seul mécanisme à deux issues
  qui s'en approche est la signature (`duerp_signer`), qui n'a qu'une
  seule issue positive (pas de « rejet »). Le Lot C introduit donc un
  **nouveau patron d'interaction** pour PSM2S, pas la réutilisation d'un
  motif existant — à concevoir, pas à copier.
- **`registre/contractualisation.py` n'existe pas.** Vérifié par
  listing du dossier `registre/`. Or l'architecture technique (§2, §3.2,
  §3.3, §4.4) prévoit explicitement les fonctions `perimetre_a_date`,
  `tarif_mensuel`, et la logique de `statut_coherent` (redirigée vers ce
  module au Lot A, cf. commentaire dans `models.py` ligne 1647-1650)
  dans un module de ce nom. **Aucune de ces fonctions n'a encore été
  écrite** — ni au Lot A (qui les avait envisagées mais volontairement
  reportées), ni au Lot B (hors périmètre). Point développé au §4.

---

## 2. Analyse point par point

### 2.1 Consultation du contrat (`contrat_detail`, `contrat_historique`)

PSM2S est mono-tenant (L3.4.4) : au plus **un seul** `ContratCommercial`
`ACTIF` à la fois (contrainte déjà portée par `clean()`, ligne 1601-1609
du modèle). Conséquence vérifiée dans le code actuel : **aucune vue
existante ne résout un objet « unique » sans `pk` dans l'URL** — toutes
les routes de `urls.py` portent un `<int:pk>` ou un `<int:etab_pk>`.
`contrat_detail` serait donc la première vue de PSM2S à afficher un
objet identifié par une requête (« le contrat actif »), pas par une clé
d'URL. Deux conséquences à trancher (cf. §5) : la forme de l'URL
(`/commercial/contrat/` sans `pk` ?), et le comportement **quand aucun
contrat `ACTIF` n'existe** (avant la toute première signature, ou après
une résiliation sans renouvellement immédiat) — cas qui ne s'est encore
jamais posé ailleurs dans l'application.

`contrat_historique` : liste des `ContratCommercial` passés, reliés par
`contrat_precedent`/`renouvellements` (déjà navigable, Lot A). Réservé à
admin/responsable_securite/gestionnaire du contrat (architecture §4.3)
— candidat naturel pour `verifier_acces_gestion_contrat`, pas
`gestionnaire_requis` seul (qui laisserait passer un directeur non
gestionnaire).

### 2.2 Renouvellement (`renouvellement_form`)

Modèle déjà prêt (Lot A) : `contrat_precedent` (self-FK, `PROTECT`),
`gestionnaire_contractuel` pré-rempli mais validation explicite
obligatoire (architecture §4.2, déjà actée). Décorateur :
`commercial_gestion_requis` (admin/responsable_securite seuls —
explicitement plus restrictif que `gestion_contrat_autorisee`, qui
inclurait le gestionnaire sortant ; l'architecture est claire sur ce
point : la réassignation reste un acte réservé au siège).

**Ambiguïté fonctionnelle relevée, non résolue par la documentation
existante** : `ContratCommercial.clean()` interdit deux contrats
`ACTIF` simultanés. Au moment du renouvellement, l'ancien contrat est
généralement encore `ACTIF` (le nouveau prend le relai à une date
future). Si le formulaire de renouvellement crée le nouveau contrat
avec `statut='ACTIF'`, `full_clean()` lèvera une `ValidationError`
immédiate. Si le nouveau est créé en `EN_ATTENTE`, **quel mécanisme
bascule l'ancien en `EXPIRE`/`RESILIE` et le nouveau en `ACTIF` au bon
moment ?** Aucun document, aucun code (cron, tâche planifiée, commande
`manage.py`) ne répond à cette question à ce stade. Deux hypothèses
possibles, à trancher par Phil avant la proposition technique :
- **Bascule manuelle** : admin/responsable_securite change le statut
  des deux contrats explicitement (le renouvellement crée seulement le
  nouveau contrat `EN_ATTENTE` ; un second geste, plus tard, l'active).
  Cohérent avec la philosophie déjà actée « jamais de correction
  automatique silencieuse, toujours un signal » (§3.1/§3.4) —
  `statut_coherent` (§4 ci-dessous) signalerait alors l'écart tant que
  personne n'a fait la bascule.
- **Bascule automatique à la date de signature/début** : nécessiterait
  une tâche planifiée, non prévue dans l'architecture ni dans le
  périmètre de P5-L1 tel que cadré jusqu'ici (§9 du plan de
  développement ne mentionne aucune tâche planifiée).

**Recommandation de cette analyse** : bascule manuelle, cohérente avec
tout ce qui a été décidé jusqu'ici — mais c'est un point de
fonctionnement, pas de détail d'implémentation, à faire trancher
explicitement plutôt que supposer.

### 2.3 Résiliation (`resiliation_form`)

Simple au regard du modèle : `statut='RESILIE'` + `date_resiliation`
obligatoire (déjà imposé par `clean()`, ligne 1610-1614) +
`motif_resiliation` (texte libre, déjà un champ du modèle). « Aucune
pénalité calculée automatiquement » : cohérent avec l'absence de toute
notion de pénalité dans le modèle `ContratCommercial` — rien à faire de
spécial, juste ne rien inventer. Décorateur naturel :
`verifier_acces_gestion_contrat` (admin/responsable/gestionnaire de CE
contrat — la résiliation est une « modification du contrat », autorisée
au gestionnaire d'après la matrice du Lot B, contrairement au
renouvellement).

### 2.4 Demande d'avenant (`demande_avenant_form`)

Le texte exact de l'écran de soumission est déjà rédigé par Phil et
validé (architecture §4.4, lignes 367-386) — rien à reconcevoir sur ce
point, seulement à implémenter. Deux entrées distinctes vers ce même
écran, identifiées dans les documents existants, non encore réconciliées
techniquement :
1. Depuis `detail_etablissement`, juste après la création d'un
   établissement (bandeau informatif prévu au plan de développement §7)
   — la ligne `AJOUT`/`ETABLISSEMENT` est pré-remplie.
2. Une demande « libre », sans création d'établissement préalable —
   notamment un `RETRAIT` seul (architecture §1.3 : « saisi librement
   pour un mouvement sans création d'établissement »).

**Point technique resté ouvert dans l'architecture elle-même** (§5.1,
non tranché autrement qu'en recommandation) : à l'ajout d'un
établissement, les bâtiments actifs doivent-ils être **proposés
automatiquement** dans le formulaire (pré-cochés, modifiables), ou
l'utilisateur les ajoute-t-il un par un ? L'architecture recommande
« proposer automatiquement » mais le qualifie elle-même de point
d'ergonomie non tranché. À trancher avant la proposition technique, car
cela détermine la structure du formulaire (un seul formulaire avec
lignes dynamiques, ou plusieurs soumissions).

**Dépendance bloquante identifiée** : l'écran affiche un calcul
« avant/après » (`perimetre_a_date` + `tarif_mensuel`, précisé dans
l'architecture elle-même comme réutilisant ces deux fonctions). Ces
fonctions **n'existent pas encore** (§1 ci-dessus, détaillé au §4).
`demande_avenant_form` ne peut pas être développé sans elles.

### 2.5 Liste des demandes (`demande_avenant_liste`)

Le plus simple des six écrans : `demandes_avenant_visibles(user)` (Lot
B) fournit déjà le queryset exact, entièrement testé. Décorateur
d'entrée : `gestionnaire_requis` (exclut factotum/prestataire, comme
partout ailleurs). Aucune ambiguïté relevée.

### 2.6 Validation / rejet (`demande_avenant_validation`)

Décorateur : `verifier_acces_gestion_contrat(user, demande.contrat_commercial)`
(Lot B, patron redirection). Validation : transaction unique créant un
`MouvementPerimetre` par `LigneDemandeAvenant` de la demande, tous à la
`date_effet_souhaitee` (architecture §1.3) — le modèle protège déjà
contre une double-validation de la même ligne (`OneToOneField`
`ligne_demande_origine`, Lot A : une deuxième tentative lèverait
`ValidationError`, protection déjà en place, pas à recoder). Rejet :
change uniquement `statut`, `validateur`, `date_traitement`,
`commentaire_validation` — aucune écriture dans `MouvementPerimetre`,
déjà garanti par construction (rien ne crée de `MouvementPerimetre` en
dehors de cette transaction précise).

« Gestion du cas où le demandeur est également le validateur autorisé »
: **déjà résolu par l'architecture**, pas une ambiguïté à lever
(§4.4, lignes 406-408) — un même utilisateur peut soumettre puis
valider sa propre demande dans la foulée, sans raccourci qui
contournerait l'objet `DemandeAvenant`. `verifier_acces_gestion_contrat`
ne fait aucune différence entre demandeur et tiers — aucun code
spécifique à écrire pour ce cas, juste ne pas en introduire un par
erreur (ex. ne pas bloquer un auto-validateur par accident).

**Point neuf pour PSM2S** (rappel du §1) : aucun écran existant
n'illustre un choix « valider/rejeter ». Deux formes possibles, à
trancher dans la proposition technique : un seul écran avec deux
boutons de soumission (`name="action" value="valider|rejeter"`), ou
deux URLs distinctes. Cette analyse ne tranche pas ce point — c'est un
choix d'implémentation, pas une question métier.

---

## 3. Tests fonctionnels à prévoir

Reprise des huit catégories demandées, avec ce qui est déjà couvert au
Lot A/B et ce qui reste propre au Lot C :

| Catégorie | Déjà couvert (Lot A/B) | Reste à couvrir au Lot C |
|---|---|---|
| Droits selon la matrice du Lot B | Fonctions de permission testées isolément (20 tests) | Les mêmes droits, mais **au niveau vue** (redirection réelle sur un GET/POST, pas seulement sur l'appel direct de la fonction) |
| Renouvellement | Historisation via `contrat_precedent` testée au niveau modèle (`test_renouvellement_historise_via_contrat_precedent`) | Le formulaire crée bien une **nouvelle** ligne (jamais de modification de l'ancienne) ; gestionnaire pré-rempli mais validation explicite requise ; comportement selon la décision du §2.2 (statut du nouveau contrat) |
| Résiliation | Contrainte `date_resiliation` obligatoire testée au niveau modèle | Le formulaire écrit `statut`/`date_resiliation`/`motif_resiliation` et rien d'autre ; aucun calcul de pénalité |
| Avenant | Modèles/contraintes testés (Lot A) ; scope de consultation testé (Lot B) | Soumission (création de la demande + des lignes) ; écran d'impact chiffré correct |
| Effet différé | `date_effet`/`date_effet_souhaitee` doivent être le 1er du mois (contrainte modèle déjà testée) | Le formulaire ne doit permettre de saisir/calculer qu'une date valide (pas de contournement par une vue laxiste) |
| Absence de prorata | — (règle de calcul, pas encore codée nulle part) | Test direct sur `tarif_mensuel` une fois écrite (§4) : le montant ne varie qu'aux dates d'effet, jamais au prorata d'un mois entamé |
| Historique | `contrat_precedent`/`renouvellements` testés au niveau modèle | `contrat_historique` affiche la bonne chaîne, dans le bon ordre, sans exposer un contrat hors périmètre à un directeur non gestionnaire |
| Cohérence `DemandeAvenant`/`MouvementPerimetre` | Contrainte d'unicité `OneToOneField` testée au niveau modèle (Lot A) | Au niveau vue : une demande `REJETEE` ne produit **jamais** de `MouvementPerimetre` ; une demande `VALIDEE` en produit **exactement un par ligne**, tous à la même `date_effet` ; `perimetre_a_date` ignore les demandes non validées (test direct sur la fonction) |

---

## 4. Fonctions de calcul manquantes — préalable au Lot C

`registre/contractualisation.py` doit être créé pour que plusieurs
écrans du Lot C fonctionnent :

- **`perimetre_a_date(contrat, date)`** (architecture §2) — reconstruit
  le périmètre en rejouant les `MouvementPerimetre`. Requis par
  `contrat_detail` (état courant), `demande_avenant_form` (simulation
  avant/après) et les tests de non-prorata.
- **`tarif_mensuel(contrat, date=aujourd'hui)`** (architecture §3.2) —
  requis par les mêmes écrans.
- **`statut_coherent`** (architecture §3.1, explicitement redirigée ici
  depuis le modèle au Lot A) — signal d'écart statut/dates, jamais de
  blocage. Utile à `contrat_detail` (affichage du signal) et
  directement lié à l'ambiguïté du §2.2 (bascule manuelle du statut au
  renouvellement).
- **Maintenance annuelle et signaux de dépassement** (architecture
  §3.3/§3.4) : utiles pour un affichage complet de `contrat_detail`,
  mais leur câblage sur le tableau de bord reste au Lot E (plan de
  développement §10) — à confirmer si leur **écriture** (sans câblage
  dashboard) entre dans le périmètre du Lot C ou reste hors sujet ici.

Ce module n'a été anticipé ni au Lot A (volontairement reporté) ni au
Lot B (hors périmètre) : son écriture doit être explicitement comptée
dans le découpage du Lot C, pas traitée comme un détail
d'implémentation d'une vue.

---

## 5. Ambiguïtés et contradictions signalées

1. **Collision de vocabulaire `Contrat` / `ContratCommercial`**
   (§1) : les URLs/noms `nouveau_contrat`/`modifier_contrat`/
   `supprimer_contrat` sont déjà pris par le contrat **prestataire**
   (Phase 4). Aucune contradiction de code (les noms proposés par
   Phil — `contrat_detail`, `contrat_historique` — ne collisionnent pas
   littéralement), mais un vrai risque de confusion pour un futur
   lecteur du code entre `Contrat` (prestataire, `etablissement`-scopé)
   et `ContratCommercial` (mono-tenant, mensuel). Recommandation : un
   préfixe d'URL explicite (`/commercial/...`) et des noms de template
   sans ambiguïté (`contrat_commercial_detail.html`, pas
   `contrat_detail.html`).
2. **Résolution de l'objet unique sans `pk`** (§2.1) : aucun précédent
   dans PSM2S pour une vue qui résout « l'objet actif » sans identifiant
   d'URL, y compris le cas où il n'en existe aucun. Comportement à
   définir (page d'accueil du module commercial avec bouton « créer le
   premier contrat » ? redirection ? message ?).
3. **Bascule de statut au renouvellement** (§2.2) : non couverte par
   l'architecture ni par aucun mécanisme existant (pas de tâche
   planifiée dans PSM2S à ce jour). Recommandation formulée (bascule
   manuelle) mais à valider explicitement, pas à décider seul.
4. **Ergonomie des bâtiments à la soumission d'une demande** (§2.4) :
   déjà signalée comme ouverte dans l'architecture technique elle-même
   (§5.1) — toujours non tranchée, reste à faire avant la proposition
   technique.
5. **Forme de l'écran valider/rejeter** (§2.6) : aucun précédent PSM2S,
   pas une question métier mais un choix d'implémentation à trancher en
   proposition technique, signalé ici pour mémoire.
6. **Périmètre exact du module `contractualisation.py`** (§4) : les
   fonctions de calcul, jamais écrites, conditionnent plusieurs écrans
   du Lot C — leur écriture doit être explicitement incluse dans le
   découpage du lot, pas traitée comme allant de soi.

Aucune contradiction avec les décisions déjà validées (Lots A/B, les
deux arbitrages du 21/09/2026) n'a été trouvée — les points ci-dessus
sont des zones non couvertes par la documentation existante, pas des
désaccords avec elle.

---

## 6. Découpage technique proposé (pour discussion, pas encore la proposition technique détaillée)

1. **C0 — `registre/contractualisation.py`** : `perimetre_a_date`,
   `tarif_mensuel`, `statut_coherent`. Aucune vue, testable seul (même
   logique que les modèles du Lot A avant leurs vues). Préalable
   obligatoire aux écrans C2/C4.
2. **C1 — Consultation** : `contrat_detail`, `contrat_historique`.
   Dépend de C0 pour l'affichage des montants/signaux.
3. **C2 — Renouvellement/résiliation** : `renouvellement_form`,
   `resiliation_form`. Dépend de l'arbitrage du §2.2 (bascule de
   statut).
4. **C3 — Demande d'avenant** : `demande_avenant_form`,
   `demande_avenant_liste`. Dépend de C0 (simulation d'impact) et de
   l'arbitrage du §2.4 (ergonomie bâtiments).
5. **C4 — Validation/rejet** : `demande_avenant_validation`. Dépend de
   C3 (rien à valider sans demande) et de l'arbitrage du §2.6 (forme de
   l'écran).

Chaque sous-lot testable indépendamment, dans cet ordre de dépendances.
Le détail (signatures, templates, migrations éventuelles) revient à la
proposition technique, une fois cette analyse validée.

---

## Points nécessitant un arbitrage DT avant la proposition technique

1. Bascule du statut ancien/nouveau contrat au renouvellement (§2.2) —
   manuelle ou automatique ?
2. Comportement de `contrat_detail` en l'absence de tout contrat actif
   (§2.1, §5.2).
3. Forme de l'URL pour l'objet unique `ContratCommercial` actif (§5.2).
4. Ergonomie des bâtiments à la soumission d'une `DemandeAvenant`
   (§2.4/§5.4), déjà ouverte dans l'architecture elle-même.
5. Périmètre exact de `contractualisation.py` au Lot C : maintenance
   annuelle et signaux de dépassement inclus ou différés au Lot E (§4).

Aucune modification de code n'a été effectuée pour produire ce document.
