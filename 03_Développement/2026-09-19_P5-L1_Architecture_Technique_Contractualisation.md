# P5-L1 — Architecture technique détaillée
## Contractualisation, tarification, périmètre

Statut : conception, aucun code engagé. Suite directe des arbitrages DT
du 19/09/2026 (voir `2026-09-19_P5-L1_Analyse_Architecture_Contractualisation.md`
pour l'analyse fonctionnelle et le détail des 10 arbitrages). Ce document
précise modèles, contraintes, règles de calcul et impacts, avant
ouverture du développement. Les 10 arbitrages fonctionnels sont
considérés comme suffisamment définis par Phil (19/09/2026) ; deux
points techniques restent ouverts (§5).

**Révision du 19/09/2026 (postérieure à la première version de ce
document)** : introduction d'un troisième objet, `DemandeAvenant`
(§1.3), qui s'intercale entre la création d'un établissement et
l'application effective d'un `MouvementPerimetre`. Décidé par Phil,
sur une proposition initialement soumise par ChatGPT et discutée avec
l'assistant. Modifie §1.2 (`MouvementPerimetre` n'est plus jamais créé
directement), §4 (matrice de permissions) et §4.4 (remplace le
« bouton raccourci » par le workflow de demande). Rien de ce qui
précède ces ajouts n'est invalidé — voir chaque section pour le détail
de ce qui change.

---

## 1. Modèles

### 1.1 `ContratCommercial`

| Champ | Type | Règle |
|---|---|---|
| `duree_engagement_mois` | `PositiveSmallIntegerField`, choices (24, 36, 48) | Fixée à la création, jamais modifiée en cours de vie (arbitrage point 2). |
| `date_debut` | `DateField` | Date d'entrée en vigueur. |
| `date_fin` | `DateField` | **Calculée**, jamais saisie : `date_debut + duree_engagement_mois` (mois calendaires, via `dateutil.relativedelta`). Recalculée et vérifiée à chaque `save()`. |
| `statut` | `CharField`, choices `EN_ATTENTE / ACTIF / RESILIE / EXPIRE` | Voir §3.1 — champ stocké mais jamais seule source de vérité. |
| `date_resiliation` | `DateField`, `null=True, blank=True` | Renseigné uniquement si `statut = RESILIE`. |
| `motif_resiliation` | `TextField`, `blank=True` | Fait constaté, pas de règle financière calculée (arbitrage point 3). |
| `tarif_etablissement_mensuel` | `DecimalField(6,2)` | Figé à la signature selon le barème en vigueur pour la durée choisie (45 / 40 / 35 €). Jamais recalculé automatiquement si le barème change plus tard. |
| `tarif_batiment_mensuel` | `DecimalField(6,2)` | Figé de la même façon (4 €, indépendant de la durée). |
| `maintenance_montant_annuel` | `DecimalField(7,2)` | 150 € par établissement, déjà réduit du taux applicable (10 %/20 % selon durée) — stocké net. |
| `date_signature` | `DateField` | Traçabilité commerciale. |
| `gestionnaire_contractuel` | `ForeignKey(Utilisateur, null=True, blank=True, on_delete=SET_NULL, related_name='contrats_geres')` | **Un seul utilisateur** désigné responsable de la gestion de ce contrat (point 8, tranché le 19/09/2026 — voir §4.2). Assignable uniquement par admin/responsable_securite. |
| `contrat_precedent` | `ForeignKey('self', null=True, blank=True, on_delete=PROTECT)` | Relie explicitement un renouvellement au contrat qu'il remplace. |
| `cree_par` | `ForeignKey(Utilisateur, null=True, on_delete=SET_NULL)` | Cohérent avec `Contrat.cree_par` existant. |
| `date_creation` / `date_maj` | `auto_now_add` / `auto_now` | Idem. |

**Contrainte d'intégrité** : au plus un `ContratCommercial` avec
`statut = ACTIF` à la fois. À valider en `clean()` (validation Django,
pas contrainte SQL, cohérent avec le style du reste du code) lors du
passage d'un contrat à `ACTIF`.

### 1.2 `MouvementPerimetre`

| Champ | Type | Règle |
|---|---|---|
| `contrat_commercial` | `ForeignKey(ContratCommercial, on_delete=PROTECT, related_name='mouvements')` | Rattache toujours le mouvement au contrat en vigueur à sa date d'effet. |
| `type_mouvement` | `CharField`, choices `AJOUT / RETRAIT` | |
| `type_objet` | `CharField`, choices `ETABLISSEMENT / BATIMENT` | |
| `etablissement` | `ForeignKey(Etablissement, null=True, blank=True, on_delete=PROTECT)` | Rempli si `type_objet = ETABLISSEMENT`. |
| `batiment` | `ForeignKey(Batiment, null=True, blank=True, on_delete=PROTECT)` | Rempli si `type_objet = BATIMENT`. |
| `etablissement_code_historique` | `CharField(max_length=50)` | **Snapshot** du code établissement au moment du mouvement (exigence explicite de reconstruction indépendante de l'état courant). |
| `nom_historique` | `CharField(max_length=200)` | Snapshot du nom (établissement ou bâtiment selon `type_objet`). |
| `date_effet` | `DateField` | Toujours le 1er du mois (validé en `clean()`). |
| `date_saisie` | `DateTimeField(auto_now_add=True)` | Distincte de `date_effet` — un mouvement peut être saisi à l'avance. |
| `auteur` | `ForeignKey(Utilisateur, null=True, on_delete=SET_NULL)` | |
| `commentaire` | `TextField(blank=True)` | |

**Contrainte d'intégrité** : validation garantissant qu'exactement un
des deux champs `etablissement`/`batiment` est renseigné, cohérent avec
`type_objet`.

**`on_delete=PROTECT`** sur `etablissement`/`batiment` (jamais
`CASCADE`) : un retrait de périmètre ne supprime jamais l'objet métier
(arbitrage point 5). Combiné aux champs `*_historique` (snapshot
texte), la reconstruction du périmètre à une date donnée ne dépend donc
**ni** de l'état actuel de l'établissement/bâtiment, **ni** même de son
existence continue en base.

**Révision (19/09/2026)** : `MouvementPerimetre` n'est **plus jamais
créé directement** par une interface utilisateur — seule la validation
d'une `DemandeAvenant` (§1.3) en produit. Champ supplémentaire :

| `ligne_demande_origine` | `ForeignKey(LigneDemandeAvenant, on_delete=PROTECT, related_name='mouvement')` | Traçabilité complète : chaque mouvement remonte à la ligne de demande qui l'a produit, donc à la demande, son demandeur et son validateur. |

### 1.3 `DemandeAvenant` et `LigneDemandeAvenant` (nouveau, 19/09/2026)

Objet de **workflow**, distinct de `MouvementPerimetre` — c'est le
point le plus important de cette révision : ne jamais transformer
`MouvementPerimetre` en objet hybride (statut + fait appliqué mélangés).
Une demande rejetée ou en attente n'est **jamais** lue par
`perimetre_a_date` (§2) — seul `MouvementPerimetre` l'est.

**`DemandeAvenant`** (l'en-tête de la demande) :

| Champ | Type | Règle |
|---|---|---|
| `contrat_commercial` | `ForeignKey(ContratCommercial, on_delete=PROTECT, related_name='demandes')` | Le contrat concerné (le contrat actif au moment de la demande). |
| `demandeur` | `ForeignKey(Utilisateur, on_delete=PROTECT, related_name='demandes_soumises')` | Qui a soumis — n'importe quel utilisateur disposant du droit de créer un établissement (`admin`/`responsable_securite`/`directeur`, même périmètre que `nouveau_etablissement`). |
| `date_demande` | `DateTimeField(auto_now_add=True)` | |
| `statut` | `CharField`, choices `EN_ATTENTE / VALIDEE / REJETEE` | **Trois statuts seulement** (tranché explicitement par Phil — pas de `DEMANDE`/`A_VALIDER` distincts, pas de `APPLIQUEE` : la présence des `MouvementPerimetre` liés en est la preuve). |
| `validateur` | `ForeignKey(Utilisateur, null=True, blank=True, on_delete=SET_NULL, related_name='demandes_traitees')` | Rempli à la validation ou au rejet. |
| `date_traitement` | `DateTimeField(null=True, blank=True)` | |
| `commentaire_validation` | `TextField(blank=True)` | Motif, notamment en cas de rejet. |
| `date_effet_souhaitee` | `DateField` | Pré-calculée au 1er du mois suivant, modifiable seulement vers une date ultérieure valide (jamais rétroactive). |

**`LigneDemandeAvenant`** (une ligne par établissement/bâtiment
concerné — même structure que `MouvementPerimetre`, en mode brouillon) :

| Champ | Type | Règle |
|---|---|---|
| `demande` | `ForeignKey(DemandeAvenant, on_delete=CASCADE, related_name='lignes')` | `CASCADE` ici (contrairement à `MouvementPerimetre`) : une ligne de demande n'a aucune existence hors de sa demande, rien à protéger. |
| `type_mouvement` | `CharField`, choices `AJOUT / RETRAIT` | |
| `type_objet` | `CharField`, choices `ETABLISSEMENT / BATIMENT` | |
| `etablissement` | `ForeignKey(Etablissement, null=True, blank=True, on_delete=PROTECT)` | |
| `batiment` | `ForeignKey(Batiment, null=True, blank=True, on_delete=PROTECT)` | |

À la validation d'une `DemandeAvenant` : une transaction crée un
`MouvementPerimetre` par `LigneDemandeAvenant`, tous à la même
`date_effet` (= `date_effet_souhaitee`), chacun référençant sa ligne
d'origine. Répond du même coup à la question ouverte du §5.1 (mouvements
de bâtiment explicites) : la structure en lignes de `DemandeAvenant`
impose déjà cette granularité — créer un établissement avec 2 bâtiments
produit une demande à 3 lignes, donc 3 `MouvementPerimetre` à la
validation, cohérent avec la recommandation déjà faite.

**Qui peut faire quoi** (remplace la ligne « MouvementPerimetre déclenché
par admin/responsable_securite » de l'arbitrage initial du point 5) :

| Action | Qui |
|---|---|
| Créer un établissement | Droit opérationnel existant (`admin`/`responsable_securite`/`directeur`) |
| Soumettre une `DemandeAvenant` | Même utilisateur que ci-dessus |
| Consulter les demandes | Selon périmètre — admin/responsable_securite/gestionnaire : toutes ; directeur : celles concernant ses établissements |
| Valider une demande | `admin`/`responsable_securite`/`gestionnaire_contractuel` du contrat actif |
| Rejeter une demande | Idem |
| Créer directement un `MouvementPerimetre` | **Personne, aucune interface** |

**Pas de raccourci, y compris pour les rôles habilités** : un
admin/responsable_securite/gestionnaire_contractuel qui ajoute lui-même
un établissement passe par exactement le même mécanisme — il crée une
`DemandeAvenant`, puis la valide, dans le même parcours (les deux
étapes peuvent s'enchaîner sans latence pour lui, mais l'objet
`DemandeAvenant` existe toujours, pour que l'audit reste uniforme quel
que soit qui a agi).

**Notifications** : hors périmètre de P5-L1 (décision explicite de
Phil, pour ne pas gonfler le lot). Une liste des demandes en attente,
visible dans l'interface pour les rôles habilités, suffit
fonctionnellement pour l'instant. Notification interne, email, rappels
: candidats pour un lot ultérieur, non retenus ici.

---

## 2. Reconstruction du périmètre à une date donnée

Fonction pure, point d'entrée unique de tout calcul (tarif, signal de
dépassement, affichage historique) :

```
perimetre_a_date(contrat_commercial, date) :
    mouvements = MouvementPerimetre.objects
        .filter(contrat_commercial=contrat_commercial, date_effet__lte=date)
        .order_by('date_effet', 'date_saisie')
    rejoue AJOUT (+1) / RETRAIT (−1) par (type_objet, objet_id)
    retourne { etablissements: {...}, batiments: {...} } — ensembles, pas
    seulement des compteurs, pour permettre l'affichage détaillé.
```

Aucune lecture de `Etablissement.actif` / `Batiment.actif` dans cette
fonction — conformément à la séparation stricte actée (arbitrage point 6).

**Point technique encore ouvert** (§5.1) : mouvements de bâtiment
explicites ou implicites à l'entrée d'un établissement dans le périmètre.

---

## 3. Règles de calcul

### 3.1 Statut vs dates (réserve technique du point 7)

Le champ `statut` reste stocké, mais n'est jamais seul juge de l'état
réel : une propriété calculée `statut_coherent` compare `statut` stocké
aux dates (`date_debut`, `date_fin`, `date_resiliation`) et signale un
écart. **Pas de correction automatique silencieuse** : seulement un
signal visible en interface (admin/responsable_securite), cohérent avec
la philosophie « jamais de blocage, toujours un signal » déjà retenue
pour le dépassement de périmètre.

### 3.2 Tarif mensuel courant

```
tarif_mensuel(contrat_commercial, date=aujourd'hui) =
    perimetre = perimetre_a_date(contrat_commercial, date)
    (nb établissements × contrat_commercial.tarif_etablissement_mensuel)
  + (nb bâtiments × contrat_commercial.tarif_batiment_mensuel)
```

Jamais stocké — toujours recalculé à la demande.

### 3.3 Maintenance annuelle

Montant = `maintenance_montant_annuel × nb établissements dans le
périmètre à la date anniversaire`, une seule fois par an (pas de
proratisation, pas de date par établissement — arbitrage validé le
17/09).

**Point technique encore ouvert** (§5.2) : date anniversaire toujours
dérivée de `date_debut`, ou saisissable séparément.

### 3.4 Signaux (jamais de blocage)

Deux signaux distincts, tous deux réservés à l'affichage
admin/responsable_securite :

- **Dépassement de périmètre** :
  ```
  etablissements_reels = Etablissement.objects.filter(actif=True).count()
  etablissements_contractuels = perimetre_a_date(contrat_actif, aujourd'hui)['etablissements']
  si etablissements_reels > etablissements_contractuels : signal
  ```
  Même logique côté bâtiments.
- **Absence de gestionnaire contractuel actif** (nouveau, point 5 de la
  décision du 19/09/2026 sur le point 8) :
  ```
  si contrat_actif.gestionnaire_contractuel est null
     ou contrat_actif.gestionnaire_contractuel.is_active == False :
     signal « Le contrat n'a plus de gestionnaire contractuel actif. »
  ```
  **Aucune révocation automatique du contrat** — il reste pleinement
  valide. Le signal invite seulement un admin/responsable_securite à
  désigner un nouveau gestionnaire. Cohérent avec `is_active` standard
  Django (désactivation d'un compte utilisateur) plutôt qu'un champ
  spécifique à créer.

---

## 4. Permissions — matrice finale (point 8, tranché le 19/09/2026)

| Utilisateur | Consultation du contrat | Modification du contrat |
|---|---|---|
| `admin` | Oui, intégrale | Oui |
| `responsable_securite` | Oui, intégrale | Oui |
| `gestionnaire_contractuel` du contrat actif | Oui, intégrale | Oui, sur ce contrat (actions contractuelles — pas les capacités générales d'un admin) |
| `directeur` non désigné gestionnaire | Limitée (§4.1) | Non |
| Autres rôles (`factotum`, `prestataire`) | Non | Non |

« Modification » se lit désormais, depuis la révision du 19/09/2026,
comme « peut valider/rejeter une `DemandeAvenant` » — jamais comme
« peut créer un `MouvementPerimetre` directement », possibilité qui
n'existe pour personne (§1.3).

### 4.1 Portée de la consultation pour un directeur non gestionnaire

Les champs globaux du contrat (durée, dates, statut, tarifs unitaires
€/établissement et €/bâtiment, maintenance unitaire) sont **identiques
quel que soit l'établissement** — les montrer à un directeur ne révèle
rien sur un établissement B ou C en particulier.

Ce qui reste réservé à admin/responsable_securite : les **agrégats sur
l'ensemble du périmètre** (nombre total d'établissements/bâtiments,
montant mensuel total de l'instance), qui révéleraient la taille de
l'organisation au-delà du seul établissement du directeur.

**Retenu** : le directeur non gestionnaire voit les champs globaux du
contrat (durée, dates, statut, tarifs unitaires, maintenance unitaire),
plus une vue scopée à son propre périmètre (`_get_etab_ids_autorises`,
même source unique de vérité que partout ailleurs dans PSM2S) — pour
son ou ses établissements uniquement : sont-ils dans le périmètre
contractuel, depuis quand, combien de leurs bâtiments y sont inclus, et
le montant que **son** établissement représente dans la facture totale
(calculable directement, tarif à taux fixe). Les agrégats globaux ne
lui sont jamais montrés.

### 4.2 Habilitation contractuelle (point 8, mécanisme retenu)

- **Un seul `gestionnaire_contractuel` par `ContratCommercial`** — pas
  de liste, pas de pluralité. Simple et « juridiquement lisible » (une
  personne responsable à un instant donné). N'empêche pas plusieurs
  personnes de consulter selon leurs droits.
- **Assignable uniquement par admin/responsable_securite.**
- **Au renouvellement** : le formulaire pré-remplit
  `gestionnaire_contractuel` avec la valeur du `contrat_precedent`,
  mais la validation est **explicite et obligatoire** — jamais de
  reconduction silencieuse. Concrètement : le champ est présenté déjà
  rempli sur le formulaire de renouvellement, l'utilisateur doit
  soumettre consciemment ce formulaire (confirmer ou changer) pour que
  le nouveau `ContratCommercial` soit créé ; aucun mécanisme ne le
  reconduit hors de cette étape.
- **Historisation automatique** : chaque `ContratCommercial` garde sa
  propre référence — l'historique reste interprétable même si le
  gestionnaire change à chaque renouvellement.
- **Départ/désactivation du gestionnaire en cours de contrat** : le
  contrat reste valide, aucune révocation automatique — signal dédié
  (§3.4). Un admin/responsable_securite peut désigner un remplaçant à
  tout moment, sans attendre le renouvellement.
- **Vérification technique** : jamais une simple vérification de
  rôle — fonction dédiée `verifier_acces_gestion_contrat(user,
  contrat_commercial)`, résolue contre l'objet, même famille que
  `verifier_acces_etablissement` (discipline IDOR déjà en place dans
  tout PSM2S).

### 4.3 Vues, formulaires, tests

- **Vues** : fiche du contrat commercial actif (lecture, adaptée au
  niveau d'accès de l'utilisateur — §4/§4.1), historique des contrats
  précédents (admin/responsable_securite/gestionnaire), formulaire de
  renouvellement (crée toujours une nouvelle ligne, ne modifie jamais
  une ligne existante, gestionnaire pré-rempli mais validation
  explicite), formulaire de mouvement de périmètre (calcul automatique
  de la prochaine `date_effet` possible), tableau de comparaison
  périmètre contractuel vs périmètre réel avec les deux signaux (§3.4).
- **Formulaires** : validation `clean()` pour `date_effet` (1er du
  mois), pour la cohérence `type_objet`/`etablissement`/`batiment`,
  pour empêcher un second `ContratCommercial` `ACTIF`, et pour exiger
  un choix explicite de `gestionnaire_contractuel` au renouvellement
  (pas de valeur par défaut acceptée sans passage par le formulaire).
- **Tests à prévoir** : historisation correcte au renouvellement
  (nouvelle ligne, `contrat_precedent` renseigné, ancien contrat
  inchangé) ; reconstruction du périmètre à une date passée,
  indépendante de l'état actuel des objets ; non-suppression de
  l'établissement/bâtiment lors d'un retrait ; calcul du tarif mensuel
  sur un périmètre évolutif ; incohérence `statut`/dates signalée sans
  blocage ; signal d'absence de gestionnaire actif (désactivation d'un
  compte gestionnaire, contrat toujours valide) ; permissions par
  niveau (`admin`/`responsable_securite`/`gestionnaire_contractuel`/
  `directeur` non gestionnaire/autres), directeur non gestionnaire
  limité à son propre périmètre (jamais 403 brut, toujours 404,
  cohérent avec `get_etablissement_ou_404`).
- **Vues/formulaires/tests supplémentaires pour `DemandeAvenant`**
  (révision du 19/09/2026) : formulaire de soumission (pré-rempli
  depuis le contexte de création d'établissement, ou saisi librement
  pour un mouvement sans création d'établissement — ex. retrait seul) ;
  liste des demandes en attente, scopée par rôle (§1.3) ; écran de
  validation/rejet avec transaction créant les `MouvementPerimetre`
  correspondants. Tests : une demande `REJETEE` ne produit jamais de
  `MouvementPerimetre` et n'est jamais lue par `perimetre_a_date` ;
  une demande `VALIDEE` produit exactement un `MouvementPerimetre` par
  `LigneDemandeAvenant`, tous à la même `date_effet` ; un
  demandeur-validateur peut traiter sa propre demande, mais l'objet
  `DemandeAvenant` existe toujours (pas de chemin de code qui la
  contourne) ; aucune vue ni endpoint ne permet de créer un
  `MouvementPerimetre` sans passer par une `DemandeAvenant` validée ;
  permissions de soumission (même périmètre que
  `nouveau_etablissement`) vs permissions de validation/rejet
  (`admin`/`responsable_securite`/`gestionnaire_contractuel` uniquement).

---

### 4.4 Interaction avec la création d'un établissement — révisée (19/09/2026)

Question initiale de Phil : `nouveau_etablissement` (vue existante,
`@gestionnaire_requis` — donc accessible à `admin`, `responsable_securite`
**et `directeur`**, vérifié dans le code) crée un établissement
opérationnel, sans lien avec le périmètre contractuel (arbitrage
point 6 — séparation stricte). Un directeur peut recevoir un nouvel
établissement de l'association et avoir le droit opérationnel de le
créer sans avoir le pouvoir contractuel d'engager le contrat.

**Décision retenue : ni simple message, ni pré-validation bloquante —
un workflow de demande (`DemandeAvenant`, §1.3).** L'établissement est
créé immédiatement, sans jamais être bloqué (cohérent avec la règle
« PSM2S signale, ne bloque jamais une action opérationnelle pour une
raison commerciale »). Ce qui change : la personne ne peut plus penser
que le périmètre contractuel est modifié par le simple fait de créer
l'établissement — elle doit explicitement soumettre une demande, dont
l'application reste suspendue à une validation séparée.

**Écran affiché au moment de la soumission** (quel que soit le rôle du
demandeur) :

```
Modification du périmètre contractuel

Vous ajoutez :
  1 établissement
  2 bâtiments

Impact tarifaire
  Abonnement actuel : 159 € HT/mois
  Nouveau montant : 203 € HT/mois
  Évolution : +44 € HT/mois

La modification prendra effet le 1er du mois suivant.
Un avenant à votre contrat sera nécessaire.

[Annuler]  [Soumettre la demande]
```

Calcul « avant/après » : simulation pure, sans écriture en base —
réutilise `perimetre_a_date` (§2) et `tarif_mensuel` (§3.2), en y
ajoutant temporairement les lignes candidates (pas encore persistées).
Aucune nouvelle fonction de calcul.

**Écran affiché au moment de la validation**, pour
admin/responsable_securite/gestionnaire_contractuel — mêmes chiffres,
plus une confirmation explicite : « Je confirme la modification du
périmètre et la préparation de l'avenant. » avant `[Valider]`/`[Rejeter]`.
Ceci remplace la case à cocher envisagée dans une version antérieure de
ce document : la trace de la décision est désormais portée par l'objet
`DemandeAvenant` lui-même (`validateur`, `date_traitement`), pas par un
champ de confirmation séparé.

**Comportement selon le rôle du demandeur** :
- **Tout demandeur** (admin/responsable_securite/gestionnaire_contractuel/
  directeur) : voit l'écran de soumission ci-dessus, crée la
  `DemandeAvenant` (statut `EN_ATTENTE`).
- **Si le demandeur a aussi les droits de validation** : peut valider sa
  propre demande dans la foulée (même écran de validation, pas de
  raccourci qui contourne l'objet — §1.3).
- **Si le demandeur n'a pas les droits de validation** (directeur non
  gestionnaire) : la demande reste `EN_ATTENTE`, visible dans la liste
  des demandes en attente pour les rôles habilités (pas de notification
  automatique, décision explicite — §1.3).

**Amélioration à noter pour le signal de dépassement (§3.4)** : tel que
défini, il compare des compteurs (« 5 établissements réels contre 4 dans
le périmètre »), ce qui ne dit pas *lequel* manque. Avec `DemandeAvenant`,
ce signal devient secondaire pour le cas nominal (une demande en attente
est déjà explicite et nominative) — il garde son utilité pour détecter
un écart qui n'aurait jamais donné lieu à une demande (import de
données, anomalie). À affiner en architecture de vue (pas un nouveau
modèle) : lister les établissements/bâtiments concernés, pas seulement
un écart chiffré.

---

## 5. Points techniques encore ouverts

### 5.1 Mouvements de bâtiment explicites ou implicites

Quand un établissement entre dans le périmètre, ses bâtiments doivent-
ils faire l'objet de mouvements `AJOUT` explicites et indépendants (une
ligne `MouvementPerimetre` par bâtiment, à la même `date_effet`), ou le
rattachement à un établissement déjà dans le périmètre suffit-il à les
compter automatiquement ?

**Recommandation** : mouvements explicites, un par objet — seule option
permettant de reconstruire fidèlement l'historique si un bâtiment est
ajouté ou retiré indépendamment de l'établissement par la suite.
L'exemple donné par Phil (01/04 : +1 établissement et +2 bâtiments)
correspondrait à 3 lignes ce jour-là. Détermine l'ergonomie du futur
écran de saisie (un mouvement « ajouter un établissement » devra
proposer d'ajouter dans la foulée ses bâtiments actifs, sans que ce
soit automatique/implicite en base).

**Reste techniquement ouvert, mais désormais cadré par la structure de
`DemandeAvenant`/`LigneDemandeAvenant` (§1.3)** : cette structure impose
déjà une ligne par objet, donc la question se réduit maintenant à une
question d'ergonomie du formulaire de soumission (proposer
automatiquement les bâtiments actifs de l'établissement, ou laisser
l'utilisateur les ajouter un par un), plus à une question de modèle de
données.

### 5.2 Date anniversaire de maintenance

Toujours dérivée de `date_debut` (jour/mois reconduits chaque année),
ou saisissable séparément ?

**Recommandation** : dérivée, pas de champ distinct — évite toute
désynchronisation, sauf raison commerciale de la dissocier.

---

*Une fois ces deux derniers points confirmés, l'architecture technique
est complète et le développement (modèles, migrations, vues,
formulaires, tests) peut être ouvert comme lot dédié.*
