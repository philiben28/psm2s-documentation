# P5-L1 — Lot C4 — Analyse d'architecture
## Validation / rejet des demandes d'avenant, génération des `MouvementPerimetre`

Statut : analyse uniquement, aucun code modifié, aucun commit. GO explicite
du DT du 24/09/2026, suite à la clôture du Lot C3 (commit `38d0b27`).
Couvre les 10 points demandés par Phil. Vérifié contre le code actuel
(`registre/models.py`, `permissions.py`, `contractualisation.py`,
`views.py`) et la documentation déjà validée : architecture technique du
19/09/2026, `DECISIONS.md` (Lots A, B, C0, C1, C2, C3), propositions
techniques C2/C3.

---

## 0. Ce qui est déjà acquis — aucune redécision nécessaire

Point important constaté en relisant l'architecture technique du
19/09/2026 (§1.3, §4, §4.2, §4.3, §4.4) : **le Lot C4 a déjà été conçu en
détail dès l'origine**, avant même l'existence de C1/C2/C3. Ce document
n'a donc pas à redéfinir le principe général, seulement à vérifier qu'il
tient toujours face au code réellement écrit en C1/C2/C3, et à
transformer les intentions déjà actées en un plan de développement
concret. Rappel de ce qui est déjà tranché et reste valable :

- **Qui valide/rejette** (architecture §1.3, tableau « qui peut faire
  quoi ») : `admin` / `responsable_securite` / `gestionnaire_contractuel`
  du contrat concerné. Aucun autre rôle.
- **Un demandeur ayant aussi les droits de validation peut valider sa
  propre demande** (§4.4) — pas de raccourci qui contournerait l'objet
  `DemandeAvenant`, mais pas d'interdiction de principe non plus.
- **Écran de validation** (§4.4) : mêmes chiffres que l'écran de
  soumission (impact avant/après), plus une confirmation explicite —
  « Je confirme la modification du périmètre... » — avant
  `[Valider]`/`[Rejeter]`. Cohérent avec le patron « deux temps, jamais
  d'écriture silencieuse » déjà utilisé en C2 (`activer_contrat`) et C3
  (`demande_avenant_form`).
- **Une transaction crée un `MouvementPerimetre` par `LigneDemandeAvenant`**,
  tous à la même `date_effet` (= `date_effet_souhaitee` de la demande),
  chacun référençant sa ligne d'origine via `ligne_demande_origine`
  (§1.3).
- **Personne ne peut créer un `MouvementPerimetre` directement** — seule
  la validation d'une `DemandeAvenant` en produit (§1.2, révision du
  19/09/2026). Aucune vue actuelle ne le fait, vérifié dans le code.
- **Modèles** : tous les champs nécessaires existent déjà depuis le Lot A
  (21/09/2026) — `DemandeAvenant.validateur`, `date_traitement`,
  `commentaire_validation`, `statut` (3 valeurs) ; `MouvementPerimetre.
  ligne_demande_origine` (`OneToOneField`, `on_delete=PROTECT`).
  **Aucune migration, aucun changement de modèle n'est nécessaire pour
  C4** — vérifié en relisant `registre/models.py` dans son état actuel.
- **Tests déjà anticipés par l'architecture** (§4.3) : une demande
  `REJETEE` ne produit jamais de `MouvementPerimetre` et n'est jamais lue
  par `perimetre_a_date` ; une demande `VALIDEE` produit exactement un
  `MouvementPerimetre` par `LigneDemandeAvenant`, tous à la même
  `date_effet` ; un demandeur-validateur peut traiter sa propre demande ;
  aucune vue ne permet de créer un `MouvementPerimetre` sans passer par
  une `DemandeAvenant` validée.

Le reste de ce document vérifie chacun des 10 points demandés à la
lumière du code réellement écrit en C1/C2/C3 (qui n'existait pas encore
le 19/09/2026), et signale les endroits où l'architecture d'origine ne
suffit plus à trancher seule.

---

## 1. Validation d'une `DemandeAvenant`

### 1.1 Qui peut valider

Confirmé par relecture de `permissions.py` : `gestion_contrat_autorisee(user,
contrat)` et `verifier_acces_gestion_contrat(user, contrat)` couvrent déjà
exactement la règle de l'architecture (admin/responsable_securite/
gestionnaire_contractuel du contrat, refus par **redirection** vers le
dashboard, jamais par exception). Ces deux fonctions existent depuis le
Lot B (21/09/2026) et n'ont encore jamais été appelées par aucune vue —
C4 serait leur premier point d'usage réel, exactement comme prévu.

**Précédent de décorateur à réutiliser** : `resiliation_form` (Lot C2)
combine déjà `@gestionnaire_requis` (large, inclut `directeur`) en
première garde, puis `verifier_acces_gestion_contrat(request.user,
contrat)` en second — ce qui laisse passer un directeur gestionnaire du
contrat, mais bloque un directeur non gestionnaire. C'est le seul
précédent des trois lots précédents qui autorise un directeur à agir
(à la différence de `renouvellement_form`/`activer_contrat`, réservés à
`commercial_gestion_requis`, qui excluent même le directeur gestionnaire
— cf. `DECISIONS.md`, Lot C2). **Proposition** : réutiliser exactement le
patron de `resiliation_form` pour `valider_demande`/`rejeter_demande`,
puisque l'architecture d'origine (§1.3) inclut explicitement le
gestionnaire_contractuel parmi les validateurs, comme pour la
résiliation. → **Signalé au DT (point à confirmer, §11)**, car c'est un
choix de cohérence entre lots, pas une évidence mécanique.

### 1.2 Contrôle que le contrat est toujours `ACTIF`

C'est le point explicitement laissé ouvert par C3 (`DECISIONS.md`, Lot
C3, point 7) : *« Validation d'une demande sur un contrat non ACTIF :
différée à C4. »* Le code actuel ne fait aujourd'hui que **signaler** ce
cas en lecture seule (`demande_avenant_liste.html`, bandeau « Non
validable »), sans jamais modifier `demande.statut`.

Ce que l'architecture ne précise pas explicitement : **le comportement
exact à la validation** quand `demande.contrat_commercial.statut !=
'ACTIF'`. Deux options possibles, non tranchées :
- **Option A — refus propre, sans écriture** : la vue `valider_demande`
  affiche un message d'erreur et redirige, exactement comme
  `activer_contrat`/`resiliation_form` refusent une action sur un
  contrat au mauvais statut. La demande reste `EN_ATTENTE` indéfiniment
  (jusqu'à un rejet manuel explicite par un rôle habilité).
- **Option B — rejet automatique** : la tentative de validation (ou un
  mécanisme séparé) fait basculer la demande à `REJETEE` avec un motif
  système explicite (« contrat devenu non actif »), pour qu'elle sorte
  de la liste des demandes en attente sans intervention manuelle.

L'architecture ne mentionne qu'un rejet **manuel** (aucun mécanisme
automatique n'est décrit nulle part dans P5-L1). → **Signalé au DT
(point à arbitrer, §11)**.

### 1.3 Contrôle que la demande est encore `EN_ATTENTE`

Aucune ambiguïté : si `demande.statut != 'EN_ATTENTE'`, refus propre,
même patron que `activer_contrat` sur un contrat qui n'est plus
`EN_ATTENTE` (message explicite, aucune écriture, redirection). Génère
naturellement le comportement attendu pour une double tentative de
validation (cf. §6 — concurrence) et pour toute tentative sur une
demande déjà `VALIDEE`/`REJETEE`.

### 1.4 Demande déjà validée ou rejetée

Couvert par 1.3 : refus propre, sans écriture, quel que soit qui tente
l'action (y compris le validateur d'origine qui rechargerait la page).
Aucun changement d'état, aucune re-création de `MouvementPerimetre`.

---

## 2. Rejet

### 2.1 Motif obligatoire ou facultatif

`DemandeAvenant.commentaire_validation` est aujourd'hui
`TextField(blank=True)` — **facultatif au niveau du modèle**, aussi bien
pour une validation que pour un rejet. L'architecture (§1.3) le décrit
comme « motif, notamment en cas de rejet », sans jamais dire s'il doit
être rendu obligatoire à l'usage (contrainte de formulaire, pas de
modèle). → **Signalé au DT (point à arbitrer, §11)** : rendre le motif
obligatoire uniquement pour un rejet (pas pour une validation) serait
cohérent avec la traçabilité attendue, mais n'a jamais été tranché
explicitement.

### 2.2 Conservation définitive de la demande

Déjà acquis (§1.3, Lot A) : trois statuts seulement, aucune suppression.
Une demande `REJETEE` reste visible dans `demande_avenant_liste` (via
`demandes_avenant_visibles`, déjà réutilisée sans modification) —
aucune vue actuelle ne filtre les demandes par statut à l'affichage,
donc rien à changer sur ce point côté C3.

### 2.3 Aucun `MouvementPerimetre` en cas de rejet

Garanti par construction : la vue de rejet ne doit exécuter qu'un
changement de `statut`/`validateur`/`date_traitement`/
`commentaire_validation` sur la `DemandeAvenant`, jamais de boucle sur
`demande.lignes`. Aucune ambiguïté — un test dédié (§10) suffit à le
garantir dans la durée.

---

## 3. Création des `MouvementPerimetre`

### 3.1 Un mouvement par établissement/bâtiment, AJOUT et RETRAIT

Déjà entièrement décrit par l'architecture (§1.3) et par la structure de
`LigneDemandeAvenant` construite en C3 (diff AJOUT/RETRAIT, un objet par
ligne). La boucle de validation est mécanique : un `MouvementPerimetre`
par `LigneDemandeAvenant` de la demande, même `type_mouvement`, même
`type_objet`, même `etablissement`/`batiment`, tous à la même
`date_effet` = `demande.date_effet_souhaitee`. Aucune ambiguïté.

### 3.2 Date d'effet

= `demande.date_effet_souhaitee`, déjà validée au 1er du mois à la
soumission (Lot C3). Un contrôle de cohérence supplémentaire est
possible à la validation (revérifier que la date n'est pas devenue
rétroactive si la validation intervient tardivement après la
soumission), mais l'architecture ne l'exige pas explicitement. →
**Signalé au DT (point à arbitrer, §11)** : que faire si
`date_effet_souhaitee` est déjà passée au moment où la demande est enfin
traitée (validation tardive) ? Bloquer, avertir sans bloquer, ou laisser
passer tel quel (un mouvement avec une `date_effet` dans le passé reste
techniquement valide pour `perimetre_a_date`) ?

### 3.3 Garantie qu'une validation ne crée jamais deux fois le même mouvement

Repose entièrement sur la combinaison de deux éléments déjà en place :
- **Le contrôle de statut (1.3)** : une fois la demande passée à
  `VALIDEE` dans la même transaction que la création des mouvements, une
  seconde tentative de validation échoue au contrôle de statut avant
  toute nouvelle écriture.
- **Le verrouillage transactionnel (§6)** : nécessaire pour fermer la
  fenêtre de course entre la lecture du statut et son écriture (cf. §6).

**Vérification faite en marge de ce point** : le contrôle anti-doublon
de C3 (`DECISIONS.md`, Lot C3, point 4) garantit qu'**au plus une**
`DemandeAvenant` `EN_ATTENTE` peut toucher un établissement/bâtiment
donné à un instant donné, sur un même contrat. Conséquence utile pour
C4, vérifiée par relecture du code C3 : deux demandes distinctes ne
peuvent jamais entrer en conflit sur le même objet au moment de la
validation — le seul risque de double écriture concerne la **même**
demande validée deux fois, pas deux demandes différentes qui se
chevaucheraient. Simplifie la garantie demandée au point 3.3 à un seul
verrou (sur la demande elle-même), pas à un verrou plus large sur le
périmètre.

---

## 4. Atomicité

Aucune ambiguïté de principe — patron déjà établi et testé en C2
(`activer_contrat`, `transaction.atomic()` + `select_for_update()` +
rollback complet vérifié par un test dédié simulant un échec en cours de
transaction). Pour C4 :

```
with transaction.atomic():
    demande = get_object_or_404(DemandeAvenant.objects.select_for_update(), pk=pk)
    [contrôles 1.2/1.3/1.4 — refus propre si échec, AUCUNE écriture]
    demande.statut = 'VALIDEE'
    demande.validateur = request.user
    demande.date_traitement = timezone.now()
    demande.save()
    for ligne in demande.lignes.all():
        MouvementPerimetre.objects.create(..., ligne_demande_origine=ligne)
```

Rollback complet garanti par `transaction.atomic()` en cas d'exception à
n'importe quelle étape (ex. `ValidationError` levée par
`MouvementPerimetre.clean()` sur une ligne incohérente) — la demande
reste `EN_ATTENTE`, aucun `MouvementPerimetre` partiel ne persiste. Même
garantie que C2, vérifiable par le même type de test (`patch` simulant
un échec à la N-ième écriture).

---

## 5. Reconstitution du périmètre — `MouvementPerimetre` reste la source de vérité

Vérifié explicitement : `perimetre_a_date` (`contractualisation.py`) ne
lit que `MouvementPerimetre`, jamais `DemandeAvenant`/
`LigneDemandeAvenant`. La validation d'une demande ne fait qu'**ajouter**
des lignes à `MouvementPerimetre` via le mécanisme déjà en place —
aucune écriture directe sur le périmètre contractuel, aucun champ de
cache/compteur à maintenir ailleurs. C4 ne introduit et ne doit
introduire aucun raccourci qui contournerait cette règle (ex. mettre à
jour un compteur dénormalisé sur `ContratCommercial` en parallèle) —
aucune ambiguïté, simple point de vérification à maintenir dans le
développement.

---

## 6. Concurrence / double validation

### 6.1 Ce qui doit être verrouillé

Le risque principal identifié (§3.3) est la **même** demande validée
deux fois simultanément (deux administrateurs cliquant sur « Valider »
à quelques millisecondes d'écart, ou un double clic/rechargement). Le
patron C2 verrouille l'objet dont le statut détermine si l'action doit
avoir lieu — ici, `DemandeAvenant.objects.select_for_update()`.

**Point ouvert, distinct du précédent C2** : faut-il *aussi* verrouiller
`ContratCommercial` (comme `activer_contrat` verrouille à la fois
l'ancien et le nouveau contrat) pour se prémunir d'une validation qui
s'exécuterait en même temps qu'un C2 (`resiliation_form`/
`activer_contrat`) changeant le statut du contrat ? Techniquement,
`select_for_update()` sur la seule `DemandeAvenant` ne bloque pas une
transaction concurrente qui modifierait `ContratCommercial` en
parallèle — la vérification 1.2 (« contrat toujours ACTIF ») pourrait
alors lire un état sur le point de changer. → **Signalé au DT (point à
arbitrer, §11)** : verrouiller uniquement la `DemandeAvenant`, ou aussi
le `ContratCommercial` concerné (`select_for_update()` sur les deux,
comme `activer_contrat` le fait déjà pour l'ancien ET le nouveau
contrat) ?

### 6.2 Limitation SQLite déjà connue

Confirmé identique à C2 : `select_for_update()` est un no-op silencieux
sur SQLite (moteur de production actuel, vérifié dans
`config/settings.py`) — aucun verrou réel n'est posé, aucune clause `FOR
UPDATE` n'est émise. La protection réelle contre la concurrence ne
s'exercerait que sur un moteur qui la supporte (MySQL/PostgreSQL).
Cohérent avec la décision déjà actée en C2 : présence du code exigée,
test dédié qui vérifie l'usage effectif de `select_for_update()` et
`skipTest()` explicitement sur SQLite plutôt que de simuler une fausse
couverture. Aucune nouvelle décision nécessaire sur ce point — même
limitation, déjà documentée et acceptée par le DT.

---

## 7. Sécurité

### 7.1 Gestionnaire contractuel autorisé à valider son contrat

Couvert par `gestion_contrat_autorisee`/`verifier_acces_gestion_contrat`
(§1.1), sans aucune fonction nouvelle à écrire.

### 7.2 Directeur non gestionnaire : pas de validation

Même couverture — `verifier_acces_gestion_contrat` refuse (redirection)
tout utilisateur qui n'est ni admin/responsable_securite, ni le
`gestionnaire_contractuel` désigné sur **ce** contrat précis. Un
directeur qui a seulement soumis une demande (droit de soumission, Lot
C3) sans être gestionnaire du contrat n'a **aucun** droit de validation
— vérifié par simple lecture du code, pas une nouvelle règle.

### 7.3 Gestionnaire d'un autre contrat : pas d'accès

Également déjà couvert : `gestion_contrat_autorisee` compare
explicitement `contrat.gestionnaire_contractuel_id` à l'utilisateur pour
**ce** contrat précis (pas un rôle global) — déjà testé au Lot B
(`test_gestionnaire_dun_autre_contrat_refuse`). S'applique
mécaniquement à C4 sans changement.

### 7.4 Aucune possibilité d'IDOR via un `pk` manipulé

C'est le point qui demande une vraie décision, pas seulement une
vérification. Deux familles de précédents existent dans PSM2S, avec des
comportements différents en cas de refus :
- **Famille « objet rattaché à un périmètre d'établissement »**
  (`get_etablissement_ou_404`, `get_prestataire_ou_404`) : refuse par
  **`Http404`**, pour ne jamais révéler l'existence de l'objet à un
  utilisateur hors périmètre.
- **Famille « objet contractuel »** (`verifier_acces_gestion_contrat`,
  utilisée par `resiliation_form`) : refuse par **redirection**, sur la
  base explicite que *« l'existence d'un `ContratCommercial` n'est un
  secret pour personne »* (mono-tenant, mêmes champs globaux visibles de
  tous les gestionnaires au sens large).

Une `DemandeAvenant` n'est **pas** dans la même situation qu'un
`ContratCommercial` : elle porte sur des établissements/bâtiments précis,
et `demandes_avenant_visibles` (Lot B) restreint déjà sa visibilité en
liste au périmètre opérationnel d'un directeur non gestionnaire — un
directeur ne doit pas nécessairement savoir qu'une demande touchant un
établissement hors de son périmètre existe. Valider/rejeter une demande
suppose déjà d'être gestionnaire du contrat (accès total à toutes les
demandes de ce contrat, sans restriction de périmètre — cf. Lot B,
`demandes_avenant_visibles`), donc ce cas précis ne pose pas de
problème : un gestionnaire de contrat voit déjà toutes les demandes de
son contrat, quel que soit son périmètre opérationnel. **Le seul cas
IDOR réel à traiter est un `pk` de `DemandeAvenant` appartenant à un
AUTRE contrat**, dont l'utilisateur n'est pas gestionnaire — déjà couvert
par 7.3 (redirection, cohérent avec le patron contractuel). → **Signalé
au DT pour confirmation simple (§11)**, pas un vrai point d'arbitrage :
proposition de garder la redirection (famille contractuelle), pas
`Http404`, par cohérence avec `resiliation_form`/`activer_contrat`.

---

## 8. Cas particulier du renouvellement

### 8.1 Demandes restées attachées à l'ancien contrat

Déjà tranché en C3 (`DECISIONS.md`, point 6) : aucun transfert
automatique, une `DemandeAvenant` `EN_ATTENTE` reste liée à son
`ContratCommercial` d'origine même après un renouvellement. Rien de
nouveau à décider ici — C4 doit seulement respecter ce fait acquis (ne
jamais réassigner `demande.contrat_commercial`).

### 8.2 Ancien contrat `EXPIRE` → demande devenue non validable

C'est exactement le point 1.2 de ce document (validation sur un contrat
non `ACTIF`) — le cas du renouvellement (`EXPIRE`) n'est qu'un cas
particulier de cette règle générale, pas un cas séparé à traiter
différemment d'une résiliation (`RESILIE`). Le même arbitrage (§1.2)
couvre les deux statuts.

### 8.3 Aucun transfert automatique

Confirmé — cohérent avec 8.1, rien à ajouter.

---

## 9. Traçabilité

Entièrement couverte par les champs déjà présents depuis le Lot A,
vérifiée dans le code actuel :
- **Qui a validé/rejeté** : `DemandeAvenant.validateur` (`ForeignKey`,
  `SET_NULL` si le compte est supprimé).
- **Date de validation/rejet** : `DemandeAvenant.date_traitement`.
- **Motif de rejet** : `DemandeAvenant.commentaire_validation` (cf. §2.1
  pour la question de son caractère obligatoire).
- **Lien demande → mouvements générés** : déjà exploité par C3
  (`demande_avenant_liste.html`, accès `ligne.mouvement` via le
  `related_name='mouvement'` de `MouvementPerimetre.
  ligne_demande_origine`, `OneToOneField`). Aucun changement nécessaire
  — C4 n'a qu'à créer les `MouvementPerimetre` avec le bon
  `ligne_demande_origine`, l'accès inverse fonctionne déjà (vérifié par
  le test C3 `test_liste_expose_le_lien_vers_le_mouvement_applique`).

Aucune ambiguïté sur ce point.

---

## 10. Tests à prévoir (plan, pas de code à ce stade)

- **Autorisation** : admin/responsable_securite/gestionnaire du contrat
  autorisés ; directeur non gestionnaire refusé ; gestionnaire d'un
  autre contrat refusé ; factotum/prestataire refusés.
- **IDOR** : `pk` d'une `DemandeAvenant` d'un contrat dont l'utilisateur
  n'est pas gestionnaire → refus (redirection, cf. §7.4).
- **Validation nominale** : demande `EN_ATTENTE` sur contrat `ACTIF` →
  statut `VALIDEE`, `validateur`/`date_traitement` renseignés, un
  `MouvementPerimetre` par `LigneDemandeAvenant`, tous à la bonne
  `date_effet`, `ligne_demande_origine` correct.
- **AJOUT et RETRAIT** : les deux types de mouvement produits
  correctement à partir d'une demande mixte.
- **Rejet nominal** : demande `EN_ATTENTE` → statut `REJETEE`, aucun
  `MouvementPerimetre` créé, `perimetre_a_date` inchangé.
- **Demande déjà traitée** : tentative de validation/rejet sur une
  demande déjà `VALIDEE`/`REJETEE` → refus propre, aucune écriture,
  aucune modification des `MouvementPerimetre` existants.
- **Contrat non `ACTIF`** : tentative de validation sur une demande dont
  le contrat est devenu `EXPIRE`/`RESILIE` → comportement conforme à
  l'arbitrage du point 1.2 (à préciser une fois tranché).
- **Atomicité/rollback** : même patron que
  `ActiverContratTests.test_rollback_complet_si_echec_en_cours_de_transaction`
  (Lot C2) — simuler un échec après l'écriture du statut mais avant la
  fin de la création des mouvements, vérifier que la demande reste
  `EN_ATTENTE` et qu'aucun `MouvementPerimetre` ne persiste.
- **Concurrence/double validation** : vérifier la présence effective de
  `select_for_update()` dans la transaction (même patron que
  `ActiverContratTests.test_select_for_update_utilise_dans_la_transaction`,
  `skipTest()` sur SQLite).
- **Cas du renouvellement** : demande restée sur l'ancien contrat après
  activation d'un renouvellement (C2) → comportement conforme à
  l'arbitrage du point 1.2, aucun transfert automatique.
- **Traçabilité** : `validateur`/`date_traitement`/
  `commentaire_validation` correctement renseignés ; `ligne.mouvement`
  accessible après validation.

---

## 11. Points nécessitant l'arbitrage du DT avant la proposition technique

1. **Décorateur de vue pour `valider_demande`/`rejeter_demande`** —
   réutiliser le patron `resiliation_form` (`@gestionnaire_requis` +
   `verifier_acces_gestion_contrat`, autorise le directeur gestionnaire
   du contrat), plutôt que le patron plus restrictif de
   `renouvellement_form`/`activer_contrat`
   (`@commercial_gestion_requis`, exclut même le directeur gestionnaire).
   (§1.1)

2. **Comportement exact à la validation d'une demande dont le contrat
   n'est plus `ACTIF`** — refus propre sans écriture (la demande reste
   `EN_ATTENTE` indéfiniment, à traiter manuellement), ou rejet
   automatique avec motif système ? (§1.2, §8.2)

3. **Motif de rejet obligatoire ou facultatif** — le modèle l'autorise
   vide aujourd'hui (`blank=True`) ; à rendre obligatoire uniquement
   pour un rejet (contrainte de formulaire, pas de modèle) ? (§2.1)

4. **`date_effet_souhaitee` déjà passée au moment d'une validation
   tardive** — bloquer, avertir sans bloquer, ou laisser passer tel
   quel ? (§3.2)

5. **Portée du verrouillage transactionnel** — verrouiller uniquement la
   `DemandeAvenant` (`select_for_update()`), ou aussi le
   `ContratCommercial` concerné, par cohérence avec le double
   verrouillage déjà en place dans `activer_contrat` ? (§6.1)

6. **Confirmation simple (pas un vrai dilemme)** — refuser l'accès à une
   `DemandeAvenant` d'un contrat non géré par **redirection** (famille
   `verifier_acces_gestion_contrat`), pas par `Http404` (famille
   périmètre établissement), par cohérence avec
   `resiliation_form`/`activer_contrat`. (§7.4)

Aucun autre point de l'analyse n'appelle de décision nouvelle — le reste
découle directement de l'architecture déjà validée (19/09/2026) et des
arbitrages déjà actés en C1/C2/C3.
