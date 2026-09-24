# P5-L1 — Lot C3 : proposition technique (pour validation DT avant développement)

Fait suite à `2026-09-24_P5-L1_Lot_C3_Analyse_Architecture.md` et aux
arbitrages du même jour (`DECISIONS.md`, à mettre à jour avec cette
proposition). Document de proposition précise, **aucun code, aucune
migration**. À valider avant tout développement du Lot C3.

Intègre les six arbitrages validés sans les rouvrir : formulaire
autonome (aucune modification de `nouveau_etablissement`/
`nouveau_batiment`) ; montants réservés à admin/responsable_securite/
gestionnaire_contractuel, jamais à un directeur non gestionnaire ;
sélection d'établissements strictement bornée au périmètre autorisé
pour un directeur, contrôlée côté serveur ; une seule `DemandeAvenant`
`EN_ATTENTE` par contrat et par établissement/bâtiment concerné ;
demande `EN_ATTENTE` sur un contrat devenu `EXPIRE`/`RESILIE` :
conservée, non validable, jamais de nouveau statut ; découpage C3
(soumission + prévisualisation + liste + consultation) / C4
(validation + rejet + génération du `MouvementPerimetre`).

---

## 1. Modèles existants utilisés (aucune modification, sauf point signalé au §7)

| Modèle | Champs mobilisés | Usage dans C3 |
|---|---|---|
| `ContratCommercial` | `statut`, `date_fin`, `demandes` (related) | Résout le contrat `ACTIF` courant ; `statut` lu pour détecter une demande devenue non validable (§9) |
| `DemandeAvenant` | `contrat_commercial`, `demandeur`, `statut`, `date_effet_souhaitee` | Créée à la confirmation (§2), jamais modifiée après (pas d'écran d'édition en C3) |
| `LigneDemandeAvenant` | `demande`, `type_mouvement`, `type_objet`, `etablissement`/`batiment` | Une ligne par objet coché — **c'est déjà, telle quelle, la capture immuable de l'état du périmètre demandé** (§7) |
| `MouvementPerimetre` | — (lecture seule via `ligne.mouvement`) | Affiché dans la liste pour une demande `VALIDEE`, jamais créé ici (C4) |
| `Etablissement`, `Batiment` | `nom`, `actif` | Liste à cocher du formulaire de soumission |

Vérifié dans le code réel (`models.py`, inchangé depuis `e090817`) :
`LigneDemandeAvenant` n'a **aucun champ modifiable après création** —
pas de `date_maj`, pas de méthode d'édition. Une fois une
`DemandeAvenant` soumise, ses lignes ne peuvent plus changer sans
créer une nouvelle demande. C'est cette immutabilité structurelle,
déjà en place, qui garantit la moitié de la règle de capture (§7) sans
rien ajouter.

---

## 2. Vues

### 2.1 `demande_avenant_form` — soumission en deux temps

Un seul nom de vue, deux comportements selon la présence du champ
caché `confirme` dans le POST — même esprit que la confirmation
groupée d'`activer_contrat` (Lot C2, Option A), adapté ici à un
formulaire qui doit d'abord collecter une sélection avant de pouvoir
la prévisualiser.

```
GET  /commercial/demandes/nouvelle/
  → contrat = ACTIF courant, sinon redirection vers commercial_accueil
    (même patron que contrat_historique, Lot C1)
  → formulaire à cocher : établissements/bâtiments actifs, restreints
    au périmètre autorisé si l'utilisateur n'est ni admin/responsable_
    securite ni gestionnaire_contractuel de ce contrat (§6)
  → rien n'est écrit

POST /commercial/demandes/nouvelle/  (sans 'confirme')
  → revalide la sélection (§9 doublons, §6 périmètre serveur, ≥ 1 ligne)
  → si invalide : ré-affiche le formulaire avec message d'erreur explicite
  → si valide : calcule l'impact (§8) et affiche l'écran de
    prévisualisation (formulaire caché, mêmes cases repostées + confirme=1)
  → rien n'est encore écrit

POST /commercial/demandes/nouvelle/  (avec 'confirme=1')
  → revalide intégralement une seconde fois (ne fait jamais confiance
    aux champs cachés repostés sans re-contrôle — la situation a pu
    changer entre les deux requêtes : doublon apparu, établissement
    désactivé, contrat expiré entre-temps)
  → si toujours valide : transaction.atomic() créant la DemandeAvenant
    (statut EN_ATTENTE) + une LigneDemandeAvenant par objet coché
  → redirige vers demande_avenant_liste avec message de succès
```

Décorateur : `@gestionnaire_requis` (même droit que
`nouveau_etablissement` — architecture §4.4, déjà tranché).

### 2.2 `demande_avenant_liste` — consultation seule

```
GET /commercial/demandes/
  → queryset = demandes_avenant_visibles(request.user)  (Lot B, inchangée)
  → pour chaque demande : ses lignes, son statut, et si VALIDEE, le
    MouvementPerimetre lié à chaque ligne (ligne.mouvement)
  → pour chaque demande EN_ATTENTE dont contrat_commercial.statut
    != 'ACTIF' : indicateur "non validable" avec motif explicite (§9)
  → aucune action d'écriture sur cette page (ni bouton Valider, ni
    Rejeter — réservé à C4)
```

Décorateur : `@gestionnaire_requis` (entrée) — le filtrage fin reste
entièrement délégué à `demandes_avenant_visibles`, comme
`demande_avenant_liste` était déjà prévue dans la proposition Lot C
initiale (whole-lot) et testée pour la fonction elle-même au Lot B.

---

## 3. Formulaires

Nouveau `registre/forms.py` : pas de `ModelForm` classique pour la
sélection (une `DemandeAvenant` n'a pas de champ "établissements" —
c'est une collection de lignes). Traitement direct de
`request.POST.getlist(...)`, même patron que `renouvellement_form`
(Lot C2, périmètre repris) pour les cases à cocher établissements/
bâtiments — **aucun nouveau mécanisme de formulaire à inventer**.

Seul élément de formulaire classique : `date_effet_souhaitee`,
pré-remplie au 1er jour du mois suivant (calculée, pas saisie
librement en valeur par défaut), modifiable uniquement vers une date
ultérieure valide (jamais rétroactive, jamais le mois courant) —
conforme à l'architecture §1.3. Validation `clean()` du modèle (1er du
mois) déjà en place, réutilisée sans modification.

---

## 4. Routes

| Route | Vue | Décorateur |
|---|---|---|
| `/commercial/demandes/` | `demande_avenant_liste` | `gestionnaire_requis` |
| `/commercial/demandes/nouvelle/` | `demande_avenant_form` | `gestionnaire_requis` |

Conforme au préfixe `/commercial/...` déjà établi. Nom de route
`demande_avenant_liste` repris tel quel de la proposition technique
Lot C initiale (whole-lot).

---

## 5. Templates

- `Templates/registre/commercial/demande_avenant_form.html` — même
  patron que `renouvellement_form.html` (Lot C2) : `form-card`,
  checklist établissements/bâtiments imbriquée (`perimetre-box`). Deux
  rendus dans le même template selon l'étape (sélection vs
  prévisualisation), via une variable de contexte `etape`
  (`'selection'` ou `'confirmation'`) plutôt que deux fichiers
  distincts — évite de dupliquer la structure de la checklist.
- `Templates/registre/commercial/demande_avenant_liste.html` — même
  patron que `contrat_historique.html` (`atable-wrap`/`atable`), une
  ligne par demande : date, statut, nombre d'établissements/bâtiments
  concernés, lien vers le(s) `MouvementPerimetre` si `VALIDEE`,
  indicateur « non validable » si `EN_ATTENTE` sur un contrat non
  `ACTIF`.
- `accueil.html`/`contrat_detail.html` — ajout d'un lien vers
  `demande_avenant_liste` (à l'image des boutons Renouveler/Activer/
  Résilier ajoutés au Lot C2), visible pour tout rôle passant
  `gestionnaire_requis`.

---

## 6. Permissions réutilisées (aucune primitive nouvelle)

| Besoin | Primitive | Origine |
|---|---|---|
| Autoriser l'accès aux deux vues | `gestionnaire_requis` | Phase 4 |
| Scoper la liste | `demandes_avenant_visibles(user)` | Lot B |
| Déterminer si les montants sont visibles (§8) | `gestion_contrat_autorisee(user, contrat)` | Lot B |
| Restreindre les établissements sélectionnables pour un directeur (§9) | `etablissements_autorises(user)` | Pré-existant (IDOR) |

`gestion_contrat_autorisee` est réutilisée pour **deux besoins
distincts mais alignés** : au Lot C1 elle décidait si un utilisateur
voit les agrégats globaux du contrat ; ici, elle décide s'il voit les
montants de la prévisualisation — **exactement la même population
(admin/responsable_securite/gestionnaire_contractuel)**, ce qui
répond directement à l'arbitrage n°2 (« cette règle doit rester
cohérente avec C1 ») sans écrire de nouvelle condition.

**Contrôle serveur, pas seulement la liste affichée (arbitrage n°3)** :
la vue calcule `etab_autorises = None si gestion_contrat_autorisee(user, contrat)
sinon etablissements_autorises(user)`. La checklist GET n'affiche que
les établissements/bâtiments dans `etab_autorises` (si non `None`).
**Indépendamment de ce filtrage d'affichage**, le traitement POST
revalide que chaque établissement/bâtiment coché appartient bien à
`etab_autorises` (si non `None`) — **avant** toute autre étape,
rejette sinon avec un message explicite. Un POST forgé avec un
établissement hors périmètre échoue donc même s'il n'apparaissait pas
dans le formulaire.

---

## 7. Capture de l'état demandé — deux options, à trancher

Consigne du 24/09/2026 : « la demande doit conserver l'état du
périmètre demandé au moment de sa soumission [...] ne doit pas être
recalculée dynamiquement [...] changer de sens sans intervention de
l'utilisateur. »

**Le périmètre demandé lui-même est déjà figé sans rien construire** :
`LigneDemandeAvenant` (une ligne par établissement/bâtiment, `AJOUT`
ou `RETRAIT`) est créée une fois à la confirmation et n'est jamais
modifiée — vérifié au §1. Une fois soumise, la liste des objets
demandés ne peut pas dériver.

**Ce qui, en revanche, dérive naturellement si on le recalcule à
l'affichage** : les **montants** (tarif avant/après, économie/surcoût)
et le **périmètre avant** (nombre d'établissements/bâtiments avant
cette demande) — tous deux dépendent de `perimetre_a_date`/
`tarif_mensuel`, qui lisent l'ensemble des `MouvementPerimetre`
existants **au moment de l'appel**. Si une autre demande est validée
entre-temps, une réaffichée de `demande_avenant_liste` recalculerait
un « avant/après » différent de celui montré à la soumission — c'est
précisément ce que la consigne interdit.

- **Option A — ne jamais réafficher de montant après soumission
  (recommandée, aucun changement de modèle).** Les montants ne sont
  calculés et montrés **qu'une seule fois**, sur l'écran de
  prévisualisation avant confirmation (§2.1, deuxième POST). Une fois
  la `DemandeAvenant` créée, `demande_avenant_liste` et toute
  consultation ultérieure n'affichent **que le contenu structurel**
  (quels établissements/bâtiments, quel sens) — jamais de montant
  recalculé. Il ne peut donc jamais y avoir de dérive, puisqu'il n'y a
  plus rien à recalculer. Cohérent avec « ne pas modifier les modèles
  sans nécessité démontrée » : aucune nécessité ici, le problème est
  évité plutôt que résolu par stockage.
- **Option B — figer les montants dans deux champs snapshot.** Ajout
  de deux champs nullables à `DemandeAvenant`
  (`montant_mensuel_avant_snapshot`, `montant_mensuel_apres_snapshot`,
  `DecimalField`, même précision que `ContratCommercial`), renseignés
  une seule fois à la confirmation (jamais réécrits ensuite), permettant
  à `demande_avenant_liste` de réafficher exactement les mêmes chiffres
  qu'au moment de la soumission, indéfiniment. Nécessite une migration
  (deux champs simples, aucune contrainte).

**Recommandation : Option A.** Elle répond à la consigne aussi
strictement que l'Option B (aucune dérive possible), sans migration ni
champ supplémentaire, et reste cohérente avec le principe déjà
appliqué à `statut_coherent`/`gestion_contrat_autorisee` : PSM2S
signale au moment pertinent, sans dupliquer une donnée qui reste
calculable à la demande. **À confirmer avant développement**, car
l'Option B reste défendable si tu veux qu'un gestionnaire retrouve,
des semaines plus tard, l'impact chiffré exact qui avait justifié une
demande encore en attente.

---

## 8. Calcul de l'impact (prévisualisation, avant confirmation uniquement)

Simulation pure, aucune écriture, réutilise `perimetre_a_date`/
`tarif_mensuel` (C0, inchangées) :

```
perimetre_avant = perimetre_a_date(contrat, date_effet_souhaitee)
tarif_avant     = tarif_mensuel(contrat, date_effet_souhaitee)

# application temporaire des lignes candidates, en mémoire seulement
etabs_apres  = perimetre_avant['etablissements'] | {ajouts} - {retraits}
batiments_apres = perimetre_avant['batiments'] | {ajouts} - {retraits}
tarif_apres  = len(etabs_apres) * contrat.tarif_etablissement_mensuel
             + len(batiments_apres) * contrat.tarif_batiment_mensuel
```

Aucune nouvelle fonction de calcul dans `contractualisation.py` : la
combinaison périmètre-avant + candidats est faite directement dans la
vue, sur des ensembles Python, sans toucher `perimetre_a_date` qui
reste une fonction pure sur les mouvements réellement enregistrés.

**Visibilité (arbitrage n°2)** : le bloc « Impact tarifaire » n'est
inclus dans le contexte template que si
`gestion_contrat_autorisee(request.user, contrat)`. Un directeur non
gestionnaire voit uniquement « Vous ajoutez : 1 établissement, 2
bâtiments » et la date d'effet — jamais `tarif_avant`/`tarif_apres`.

---

## 9. Règle des doublons

**Interprétation retenue** (la consigne dit « même périmètre de
modification », lecture possible stricte ou large — tranchée ici pour
la robustesse) : au moment de la confirmation, pour **chaque**
établissement/bâtiment candidat, on vérifie qu'**aucune**
`LigneDemandeAvenant` d'une `DemandeAvenant` `EN_ATTENTE` sur le
**même contrat** ne porte déjà sur ce même établissement/bâtiment —
**quel que soit le sens** (`AJOUT` ou `RETRAIT`). Une correspondance
exacte sur l'ensemble complet (et seulement l'ensemble complet)
laisserait passer un chevauchement partiel (ex. une demande en attente
sur `{A, B}` n'empêcherait pas une nouvelle demande sur `{B, C}`),
ce qui contredit l'objectif (deux demandes concurrentes touchant le
même objet). **À confirmer** : cette lecture par recouvrement, plus
stricte que « ensemble strictement identique », est-elle bien celle
voulue ?

```
conflits = LigneDemandeAvenant.objects.filter(
    demande__contrat_commercial=contrat,
    demande__statut='EN_ATTENTE',
).filter(
    Q(etablissement_id__in=etabs_candidats) | Q(batiment_id__in=batiments_candidats)
)
if conflits.exists():
    # refus explicite, liste les objets en conflit et la/les demande(s)
    # d'origine — aucune DemandeAvenant créée
```

**Purement applicatif, aucune contrainte SQL** (conforme à la
consigne — une contrainte d'unicité partielle en base ferait l'objet
d'une proposition séparée si jamais nécessaire). Vérifié aux deux
POST (sélection et confirmation) pour donner un retour dès la
première étape plutôt qu'à la toute fin.

**Après `REJETEE`** : aucune ligne `EN_ATTENTE` ne subsiste pour cet
objet — une nouvelle demande est acceptée sans condition particulière.
**Après `VALIDEE`** : idem, la demande n'est plus `EN_ATTENTE`, elle
ne bloque plus rien — une nouvelle demande constitue un nouveau cycle,
comme précisé dans l'arbitrage.

---

## 10. Cas du contrat devenu EXPIRE/RESILIE

**Aucun nouveau statut, aucune écriture automatique** (conforme à
l'arbitrage n°5). Purement une lecture dérivée, au moment de
l'affichage :

```
demande.contrat_commercial.statut != 'ACTIF'
```

Si vrai pour une demande `EN_ATTENTE` : `demande_avenant_liste`
affiche un motif explicite, par exemple *« Ce contrat n'est plus actif
(statut : Expiré) — cette demande ne peut plus être validée »*, sans
modifier `demande.statut` ni aucun champ. La demande reste
historiquement consultable, comme n'importe quelle autre.

**Application différée à C4** : c'est la vue de validation (non
construite ici) qui devra refuser explicitement de valider une telle
demande — signalé pour que ce cas soit repris explicitement dans
l'analyse C4, pas oublié entre les deux lots.

**Nouveau cas signalé, propre à l'interaction C2 × C3, non couvert par
l'arbitrage n°5 littéralement** : que se passe-t-il si, après le
renouvellement (Lot C2), un **nouveau** contrat devient `ACTIF`, et
qu'une `LigneDemandeAvenant` d'une ancienne demande `EN_ATTENTE`
(rattachée à l'ancien contrat, maintenant `EXPIRE`) porte sur un
établissement qui existe aussi dans le nouveau contrat ? Rien ne relie
automatiquement l'ancienne demande au nouveau contrat — **elle reste
orpheline de l'ancien contrat, jamais transférée**, ce qui semble
cohérent avec « elle devient non validable » (elle concerne un
contrat révolu, pas le nouveau). Un utilisateur souhaitant le même
changement sur le nouveau contrat devra soumettre une **nouvelle**
demande. Comportement qui découle naturellement de la règle déjà
arbitrée, présenté ici pour confirmation explicite plutôt que supposé.

---

## 11. Matrice des droits

| Action | admin / responsable_securite | gestionnaire_contractuel (contrat actif) | Directeur non gestionnaire | Autres rôles |
|---|---|---|---|---|
| Soumettre une demande | Oui | Oui | Oui (établissements de son périmètre uniquement) | Non |
| Voir les montants en prévisualisation | Oui | Oui | Non | — |
| Consulter la liste (scope) | Toutes | Toutes celles de son contrat | Celles de son périmètre | Non |
| Valider / rejeter (C4, rappel) | Oui | Oui, sur son contrat | Non | Non |

---

## 12. Stratégie de tests

### 12.1 Soumission
- Contrat `ACTIF` requis : redirection vers `commercial_accueil` sinon.
- Étape 1 (sélection) → étape 2 (prévisualisation) : aucune écriture
  avant `confirme=1`.
- Confirmation : `DemandeAvenant` + `LigneDemandeAvenant` créées
  correctement (statut `EN_ATTENTE`, `demandeur`, lignes conformes à
  la sélection).
- Au moins une ligne requise (demande vide refusée).

### 12.2 Permissions
- admin/responsable_securite/gestionnaire_contractuel/directeur
  autorisés à soumettre ; factotum/prestataire refusés.
- Directeur non gestionnaire : établissements hors périmètre absents
  de la checklist **et** rejetés si forcés en POST direct (test IDOR
  explicite, même esprit que les tests C4-1/C4-7 déjà en place
  ailleurs dans PSM2S).
- Montants présents dans le contexte pour admin/responsable/
  gestionnaire ; absents pour un directeur non gestionnaire.
- Liste : reprise directe du scope déjà testé pour
  `demandes_avenant_visibles` (Lot B) — vérifier que la vue restitue
  exactement ce résultat.

### 12.3 Impact
- Périmètre avant/après correct pour un ajout, pour un retrait, pour
  un mélange établissement + bâtiment.
- Montants avant/après corrects (établissement et bâtiment,
  tarifs distincts).

### 12.4 Doublons
- Deuxième soumission sur un établissement déjà présent dans une
  demande `EN_ATTENTE` du même contrat → refusée.
- Après rejet de la première → nouvelle soumission acceptée.
- Après validation de la première (créée directement en fixture, sans
  passer par une vue de validation qui n'existe pas encore) → nouvelle
  soumission acceptée.

### 12.5 Contrat non `ACTIF`
- Une `DemandeAvenant` `EN_ATTENTE` fixée en base sur un contrat rendu
  `EXPIRE` (même technique que les tests d'activation du Lot C2 —
  dates relatives à `timezone.now()`, jamais une date calendaire
  figée) : `demande_avenant_liste` affiche le motif de non-validité,
  sans modifier `demande.statut`.

### 12.6 Absence d'écriture prématurée
- Après l'étape 1 (sélection) et l'étape 2 (prévisualisation, sans
  confirmer) : `DemandeAvenant.objects.count()` et
  `MouvementPerimetre.objects.count()` strictement inchangés.
- Après confirmation : `MouvementPerimetre.objects.count()` **toujours
  inchangé** — seule une future action C4 en créera.

### 12.7 Historisation
- `demande.lignes.all()` accessible et correcte pour une demande
  quel que soit son statut.
- Pour une demande `VALIDEE` créée directement en fixture avec ses
  `MouvementPerimetre` déjà liés (simulant ce que produira C4) :
  `ligne.mouvement` accessible depuis la liste, sans requête
  supplémentaire non prévue.

---

## Nouvelles ambiguïtés signalées dans cette proposition

1. **Capture de l'état demandé** (§7) : Option A (ne jamais réafficher
   de montant après soumission, recommandée) vs Option B (deux champs
   snapshot, migration mineure).
2. **Granularité de la règle des doublons** (§9) : recouvrement objet
   par objet (recommandé) vs correspondance exacte de l'ensemble
   complet.
3. **Demande orpheline après renouvellement** (§10) : confirmation que
   l'ancienne demande reste liée à l'ancien contrat (jamais transférée
   au nouveau), une nouvelle demande devant être soumise séparément.
4. **Application du refus de validation pour contrat non `ACTIF`**
   (§10) : à traiter explicitement dans l'analyse C4, signalé ici pour
   ne pas être oublié entre les deux lots.

---

## Fichiers qui seraient modifiés (développement futur — aucun changement maintenant)

- `registre/views.py` — `demande_avenant_form`, `demande_avenant_liste`.
- `registre/urls.py` — 2 routes.
- `registre/tests.py` — nouvelles classes de tests (§12).
- Nouveaux templates `Templates/registre/commercial/demande_avenant_form.html`,
  `demande_avenant_liste.html`.
- `Templates/registre/commercial/accueil.html`/`contrat_detail.html` —
  lien vers la liste des demandes.
- `registre/models.py` — **uniquement si l'Option B est retenue au
  §7** (deux champs nullables sur `DemandeAvenant`, migration mineure).
- `registre/forms.py` — pas de nouveau `ModelForm` nécessaire (§3).

Aucun changement à `registre/permissions.py` ni
`registre/contractualisation.py`.

---

## Prochaine étape

Confirmation des quatre points signalés (§7 à §10), puis GO explicite
pour le développement de C3 — même méthode que les lots précédents :
implémentation, `manage.py check`, tests C3 ciblés, suite complète,
`makemigrations --check --dry-run` (uniquement pertinent si l'Option B
est retenue), rapport, validation DT, commit.
