# P5-L1 — Lot C2 : proposition technique (pour validation DT avant développement)

Fait suite à `2026-09-21_P5-L1_Lot_C2_Analyse_Architecture.md` et aux
arbitrages du 24/09/2026 (`DECISIONS.md`, section « P5-L1 — Lot C2 »).
Document de proposition précise, **aucun code, aucune migration**. À
valider avant tout développement du Lot C2.

Intègre les sept arbitrages validés sans les rouvrir : résiliation
dans C2 ; périmètre repris en pré-remplissage modifiable, jamais
appliqué automatiquement ; tarifs pré-remplis ; activation impossible
avant la fin de l'ancien contrat ; Option A pour `activer_contrat` ;
refus propre sur statut invalide ; `select_for_update()` à l'activation,
sans mécanisme de concurrence plus lourd. **Aucune contrainte SQL
supplémentaire n'est proposée ici**, conformément à la consigne — elle
ferait l'objet d'une proposition séparée si elle devait un jour être
envisagée.

---

## 1. Vue d'ensemble des routes

| Route | Vue | Décorateur | Rôle |
|---|---|---|---|
| `/commercial/contrat/renouveler/` | `renouvellement_form` | `commercial_gestion_requis` | Crée un nouveau `ContratCommercial` (`EN_ATTENTE`). Accessible même en l'absence de tout contrat (= création du tout premier contrat). |
| `/commercial/contrat/<int:pk>/activer/` | `activer_contrat` | `commercial_gestion_requis` | Bascule atomique : ancien `ACTIF` → `EXPIRE`, contrat `pk` `EN_ATTENTE` → `ACTIF`. |
| `/commercial/contrat/<int:pk>/resilier/` | `resiliation_form` | `verifier_acces_gestion_contrat` (pas `commercial_gestion_requis`) | Statut `RESILIE` + `date_resiliation` + `motif_resiliation`. |

Reprises telles que déjà esquissées dans la proposition technique Lot C
(whole-lot). **Asymétrie délibérée, pas un oubli** : `renouvellement_form`
et `activer_contrat` sont réservés à admin/responsable_securite
(`commercial_gestion_requis`) — ce sont des actions qui ne dépendent pas
d'un contrat précis déjà résolu, ou qui engagent une décision
structurante (cf. docstring `commercial_gestion_requis`, Lot B).
`resiliation_form` porte sur un contrat précis déjà résolu et reste donc
ouverte au `gestionnaire_contractuel` de ce contrat, via
`verifier_acces_gestion_contrat` — cohérent avec la matrice de
l'architecture technique (§4 : « Modification » ouverte au gestionnaire
sur son contrat) et avec la docstring de `verifier_acces_gestion_contrat`
elle-même, qui cite la résiliation comme cas d'usage prévu.

---

## 2. `renouvellement_form` — création avec pré-remplissage

### 2.1 Champs du contrat

Nouveau `ContratCommercialForm` (`registre/forms.py`, même convention
que `ContratForm`/`PrestataireForm` — `ModelForm` + `__init__`
personnalisé pour les valeurs initiales) :

| Champ | Pré-remplissage | Obligatoire |
|---|---|---|
| `duree_engagement_mois` | Aucun (choix explicite à chaque renouvellement) | Oui |
| `date_debut` | Aucun (saisie explicite) | Oui |
| `date_signature` | Aucun | Oui |
| `tarif_etablissement_mensuel` | Valeur du contrat précédent | Oui, modifiable |
| `tarif_batiment_mensuel` | Valeur du contrat précédent | Oui, modifiable |
| `maintenance_montant_annuel` | Valeur du contrat précédent | Oui, modifiable |
| `gestionnaire_contractuel` | Valeur du contrat précédent | Oui, modifiable — jamais retenu hors soumission explicite (architecture §4.2, déjà validée) |

`statut` n'est **pas** un champ du formulaire (toujours forcé à
`EN_ATTENTE` côté vue, jamais exposé à la saisie — cohérent avec le
principe déjà retenu pour Lot A : aucune incohérence possible par
construction). `contrat_precedent` est renseigné automatiquement par
la vue (contrat `ACTIF` courant s'il existe, sinon `None` pour le tout
premier contrat) — pas un champ du formulaire non plus.

### 2.2 Pré-remplissage du périmètre — distinction pré-remplissage / application effective

**Pré-remplissage (affichage seul, rien n'est écrit en base)** : la vue
calcule `perimetre_a_date(contrat_precedent, timezone.now().date())`
(C0, déjà disponible) et affiche une liste à cocher de tous les
établissements/bâtiments connus du système, **pré-cochés** pour ceux
présents dans ce périmètre. Rien de cet état n'est stocké tant que le
formulaire n'est pas soumis — un rechargement de page sans soumission
ne modifie rien.

**Application effective (à la soumission du formulaire)** : le
`ContratCommercial` (`EN_ATTENTE`) et les objets périmètre sont créés
**dans la même transaction** :

1. Le nouveau contrat est enregistré (`EN_ATTENTE`).
2. Une `DemandeAvenant` est créée, rattachée à ce nouveau contrat
   (`demandeur=request.user`, `date_effet_souhaitee` = premier jour du
   mois du nouveau `date_debut` — voir §2.3 sur cette contrainte), avec
   une `LigneDemandeAvenant` de type `AJOUT` pour chaque
   établissement/bâtiment resté coché à la soumission (qu'il ait été
   pré-coché ou ajouté manuellement — aucune distinction technique
   entre reprise inchangée et ajout volontaire à ce niveau : les deux
   produisent une ligne `AJOUT`, il n'y a jamais de `RETRAIT` sur un
   contrat neuf qui n'a encore aucun mouvement).
3. Cette `DemandeAvenant` est **validée dans la foulée, par le même
   utilisateur, dans la même transaction** (`statut='VALIDEE'`,
   `validateur=request.user`, `date_traitement=timezone.now()`), ce qui
   produit un `MouvementPerimetre` par ligne — via la même logique que
   celle prévue pour l'écran de validation de C4 (non développée ici en
   tant qu'écran séparé, seulement comme fonction interne réutilisée).

**Pourquoi une validation immédiate plutôt qu'un dépôt en attente,
alors que `MouvementPerimetre` ne doit jamais être créé autrement que
par la validation d'une `DemandeAvenant`** (invariant du modèle, Lot A,
`ligne_demande_origine` non nul) : la personne qui exécute
`renouvellement_form` est nécessairement admin/responsable_securite
(§1) — exactement la même population autorisée à valider une
`DemandeAvenant` en temps normal. Il n'y a donc aucune séparation des
pouvoirs à préserver en imposant un second passage par un écran de
validation qui n'existe pas encore (C4). La `DemandeAvenant` est bien
créée et passe bien par une validation en bonne et due forme — la
structure et la traçabilité de l'invariant sont respectées — seule la
validation elle-même est immédiate plutôt que différée.

**Ceci reste conforme à « rien n'est encore contractuellement
appliqué »** (formulation de la consigne) : ce qui n'est *pas* encore
appliqué au moment du pré-remplissage, c'est le **contrat lui-même**,
qui reste `EN_ATTENTE` jusqu'à `activer_contrat` — la présence de
`MouvementPerimetre` rattachés à un contrat encore `EN_ATTENTE` ne
produit aucun effet contractuel tant que ce contrat n'est pas devenu
`ACTIF` (rien dans `perimetre_a_date`/`tarif_mensuel` ne les traite
différemment selon le statut du contrat, mais aucune vue ne les
expose comme actifs pour un contrat non-`ACTIF` — `contrat_detail`
affiche ces données pour n'importe quel contrat consulté, comme
aujourd'hui pour l'historique).

**Point signalé, non tranché ici** : cette conception résout
l'ambiguïté en choisissant l'auto-validation systématique (reprise
inchangée **et** périmètre modifié). Une alternative rejetée aurait
été de ne valider immédiatement que la reprise strictement inchangée,
et de laisser toute modification en `EN_ATTENTE` jusqu'à un futur écran
C4 — écartée ici car elle ferait dépendre C2 de C3/C4 pour un cas
d'usage courant (modifier le périmètre en renouvelant), ce qui semble
contraire à l'esprit de livrer C2 de façon autonome. **Mérite
confirmation explicite avant développement**, car elle touche
directement le workflow `DemandeAvenant`.

### 2.3 Point technique signalé — `date_debut` et le 1er du mois

`MouvementPerimetre.date_effet` doit obligatoirement être le 1er du
mois (`clean()`, déjà en place). Si `date_effet` de la reprise est
calé sur `nouveau.date_debut`, cela impose indirectement que
`date_debut` du nouveau contrat soit lui-même le 1er du mois — **alors
qu'aucune règle de ce type n'existe aujourd'hui sur
`ContratCommercial.date_debut`**. Deux options, non tranchées :

- **Option 1** : imposer `date_debut` au 1er du mois pour tout
  `ContratCommercial` (nouvelle règle `clean()`, pas une contrainte
  SQL — n'entre donc pas dans l'interdiction de la consigne, mais
  reste un changement de règle métier sur le modèle, à valider
  explicitement).
- **Option 2** : caler `date_effet` de la reprise sur le 1er jour du
  mois de `date_debut` (ou le mois suivant si `date_debut` n'est pas
  le 1er), indépendamment de la date exacte de `date_debut`. Plus
  souple, mais un contrat pourrait démarrer un 15 du mois avec un
  périmètre qui ne prend effet que le 1er du mois suivant — décalage à
  assumer explicitement.

**Recommandation** : Option 1, plus simple et cohérente avec le
principe déjà retenu ailleurs dans P5-L1 (dates de périmètre toujours
au 1er du mois, sans exception). **À confirmer avant développement.**

---

## 3. `resiliation_form`

Formulaire minimal (`ContratResiliationForm`, nouveau, deux champs :
`date_resiliation`, `motif_resiliation`) sur un contrat précis
(`pk` dans l'URL, normalement le contrat `ACTIF`, mais la vue ne
l'impose pas explicitement — `verifier_acces_gestion_contrat` gère
l'accès, `ContratCommercial.clean()` exige déjà `date_resiliation` si
`statut='RESILIE'`). Écrit uniquement `statut='RESILIE'` +
`date_resiliation` + `motif_resiliation` sur le contrat visé — aucune
transaction complexe, aucun impact sur un autre contrat (contrairement
à `activer_contrat`). Ne touche à aucun `MouvementPerimetre`.

---

## 4. `activer_contrat` — bascule atomique

### 4.1 Séquence

```
POST /commercial/contrat/<pk>/activer/
        │
        ▼
BEGIN transaction.atomic()
        │
        ▼
nouveau = ContratCommercial.objects.select_for_update().get(pk=pk)
        │
        ▼
nouveau.statut == 'EN_ATTENTE' ?  ──── non ──→ refus explicite, rollback, message
        │ oui
        ▼
ancien = ContratCommercial.objects.select_for_update()
              .filter(statut='ACTIF').first()
        │
        ▼
ancien existe et aujourd'hui < ancien.date_fin ? ── oui ──→ refus explicite
        │                                                    (« le contrat en
        │ non (ou pas d'ancien : premier contrat)             cours n'expire
        ▼                                                      que le JJ/MM/AAAA »)
ancien existe ?
   │ oui                              │ non (premier contrat)
   ▼                                  │
ancien.statut = 'EXPIRE'              │
ancien.save()                         │
   │                                  │
   └──────────────┬───────────────────┘
                   ▼
       nouveau.statut = 'ACTIF'
       nouveau.save()
                   ▼
                COMMIT
```

En cas d'échec à n'importe quelle étape après le début de la
transaction (`ValidationError` sur l'un des deux `save()`, exception
quelconque), **rollback complet** : `ancien` reste `ACTIF`, `nouveau`
reste `EN_ATTENTE` — jamais d'état intermédiaire persistant, exactement
le schéma demandé par la consigne.

### 4.2 `select_for_update()`

Deux verrous pris au tout début de la transaction, avant toute
vérification :

- `ContratCommercial.objects.select_for_update().get(pk=pk)` — verrouille
  le contrat à activer, pour empêcher deux activations concurrentes du
  même contrat.
- `ContratCommercial.objects.select_for_update().filter(statut='ACTIF')`
  — verrouille le(s) contrat(s) actuellement `ACTIF` (0 ou 1 en
  pratique), pour empêcher qu'une seconde transaction lise « aucun
  `ACTIF` » avant que la première n'ait committé son `EXPIRE`.

Toute tentative d'activation concurrente est ainsi sérialisée par la
base de données — la seconde transaction attend la fin de la première
avant de relire l'état réel des contrats, plutôt que de risquer de
passer la vérification `clean()` sur un état déjà obsolète.

**Portabilité** : `select_for_update()` est un no-op silencieux sur
SQLite (utilisé par les tests) — aucun verrou réel n'est pris, mais
aucune erreur non plus ; le comportement transactionnel (atomicité,
rollback) reste testable normalement. Sur le moteur de production
(à confirmer selon la configuration Passenger/o2switch), le verrou est
réellement posé.

### 4.3 Gestion des statuts invalides

`activer_contrat` refuse proprement, sans aucune écriture, dans les
cas suivants :

- `nouveau.statut != 'EN_ATTENTE'` (déjà `ACTIF`, `EXPIRE` ou
  `RESILIE`) → message explicite (« Ce contrat n'est plus activable,
  son statut actuel est *statut affiché*. »), redirection vers
  `contrat_detail`.
- Un contrat `ACTIF` existe et sa `date_fin` n'est pas encore atteinte
  → message explicite nommant la date d'expiration réelle.

Dans les deux cas : aucune transaction n'est ouverte au-delà de la
lecture (`select_for_update` peut avoir déjà verrouillé les lignes,
mais rien n'est modifié — la transaction se termine sans écriture, ce
qui équivaut à un rollback trivial).

---

## 5. Contrôles métier — récapitulatif

| Contrôle | Où | Mécanisme |
|---|---|---|
| Durée (24/36/48 mois) | `ContratCommercialForm` | `choices`, déjà porté par le modèle |
| Un seul `ACTIF` | `ContratCommercial.clean()` (existant) + ordre des écritures + `select_for_update` (§4) | Déjà en place, complété par le verrouillage |
| Statut invalide pour activation | `activer_contrat` | Vérification explicite avant toute écriture (§4.3) |
| Date d'activation prématurée | `activer_contrat` | Comparaison `timezone.now().date()` vs `ancien.date_fin` (§4.1) |
| Cohérence statut/dates a posteriori | `statut_coherent` (C0, existant) | Réutilisé tel quel dans `contrat_detail` (C1, déjà en place) — pas de nouvelle règle pour C2 |
| Gestionnaire contractuel | `ContratCommercialForm` | Pré-rempli, requis, modifiable (§2.1) |
| `date_debut` au 1er du mois | À confirmer (§2.3) | Nouvelle règle `clean()` si Option 1 retenue |

---

## 6. Permissions — récapitulatif

| Action | admin / responsable_securite | Gestionnaire du contrat | Directeur non gestionnaire | Autres rôles |
|---|---|---|---|---|
| `renouvellement_form` | Oui | Non | Non | Non |
| `activer_contrat` | Oui | Non | Non | Non |
| `resiliation_form` | Oui | Oui, sur son contrat (`verifier_acces_gestion_contrat`) | Non | Non |

Aucune nouvelle fonction de permission nécessaire — `commercial_gestion_requis`
et `verifier_acces_gestion_contrat` (Lot B) suffisent aux trois vues.

---

## 7. Historisation — conservation intégrale

- **Renouvellement** : l'ancien contrat n'est touché par aucune
  écriture (§2.1). Sa ligne reste identique, à tout moment, avant et
  après le renouvellement.
- **Activation** : la seule écriture sur l'ancien contrat est
  `statut='EXPIRE'` — aucun autre champ n'est modifié (dates, tarifs,
  gestionnaire, mouvements de périmètre déjà rattachés restent
  intacts).
- **Résiliation** : écrit uniquement sur le contrat visé
  (`statut`, `date_resiliation`, `motif_resiliation`) — jamais sur un
  autre contrat.
- **Chaîne de traçabilité** : `contrat_precedent`/`renouvellements`
  (Lot A, déjà en place) relie chaque contrat à son prédécesseur —
  aucun ajout nécessaire au modèle pour cette chaîne.
- **`MouvementPerimetre`** : chaque contrat a ses propres mouvements
  (`FK contrat_commercial`) — un renouvellement n'écrit jamais sur les
  mouvements de l'ancien contrat, même quand le périmètre repris est
  identique (§2.2 : nouvelles lignes `AJOUT` sur le nouveau contrat,
  jamais de réécriture des mouvements existants).
- **Aucune suppression**, à aucune étape de C2.

---

## 8. Tests à ajouter dans `registre/tests.py`

### 8.1 Création / renouvellement

- Contrat créé en `EN_ATTENTE`, jamais `ACTIF`, quel que soit le
  contexte.
- `contrat_precedent` correctement lié au contrat `ACTIF` courant, ou
  `None` pour le tout premier contrat de l'instance.
- Ancien contrat strictement inchangé après création du nouveau
  (comparaison champ à champ avant/après).
- Tarifs et gestionnaire pré-remplis avec les valeurs de
  `contrat_precedent`, mais le formulaire les accepte modifiés.
- Coexistence `ACTIF` (ancien) + `EN_ATTENTE` (nouveau) acceptée sans
  erreur.

### 8.2 Périmètre repris

- Périmètre inchangé à la soumission → `MouvementPerimetre` créés sur
  le **nouveau** contrat, identiques (mêmes établissements/bâtiments)
  à ceux de l'ancien à la date du jour ; `DemandeAvenant` associée en
  `VALIDEE`.
- Périmètre modifié (ajout/retrait avant soumission) → mêmes
  mécanismes, mais lignes `AJOUT` reflétant l'état final coché, pas
  l'état pré-rempli.
- Aucun `MouvementPerimetre` créé ou modifié sur l'**ancien** contrat.
- `perimetre_a_date(nouveau, ...)` reflète bien la reprise dès sa
  création (C0, réutilisé sans modification).

### 8.3 Activation

- Bascule complète : ancien `EXPIRE`, nouveau `ACTIF`, en une seule
  transaction.
- Cas du premier contrat (`contrat_precedent=None`) : activation sans
  ancien à basculer.
- Refus si `nouveau.statut != 'EN_ATTENTE'` (tester les trois autres
  statuts) — aucune écriture produite.
- Refus si `ancien.date_fin` n'est pas encore atteinte — aucune
  écriture produite, ancien reste `ACTIF`, nouveau reste `EN_ATTENTE`.

### 8.4 Atomicité et concurrence

- **Rollback complet** : simuler un échec du second `save()` (ex. via
  mock ou signal) après le premier — vérifier que l'ancien contrat est
  bien resté `ACTIF` en base (pas de commit partiel). Test le plus
  important de ce lot.
- **Verrouillage** : vérifier que `select_for_update()` figure bien
  dans les requêtes émises par `activer_contrat` (`CaptureQueriesContext`
  ou équivalent, sur un backend qui le supporte). Un test de
  concurrence réelle (deux threads, `TransactionTestCase`) est
  techniquement possible mais introduirait un patron de test absent du
  reste de la suite (qui n'utilise que `TestCase`, jamais de threads) —
  **signalé, pas recommandé par défaut** ; à discuter si un niveau de
  preuve supplémentaire est souhaité.

### 8.5 Résiliation

- Statut `RESILIE` + `date_resiliation` + `motif_resiliation` corrects
  après soumission.
- Refus si `date_resiliation` absente (déjà garanti par
  `ContratCommercial.clean()`, à vérifier via la vue).
- Permissions : admin/responsable_securite et gestionnaire du contrat
  autorisés ; directeur non gestionnaire et autres rôles refusés.

### 8.6 Permissions (les trois vues)

- admin/responsable_securite : accès aux trois vues.
- Gestionnaire du contrat : accès à `resiliation_form` sur son
  contrat, refus sur `renouvellement_form`/`activer_contrat`.
- Directeur non gestionnaire, factotum, prestataire : refus sur les
  trois.

---

## 9. Fichiers qui seraient modifiés (développement futur — aucun changement maintenant)

- `registre/forms.py` — nouveau `ContratCommercialForm`, nouveau
  `ContratResiliationForm`.
- `registre/views.py` — nouvelles vues `renouvellement_form`,
  `activer_contrat`, `resiliation_form`.
- `registre/urls.py` — trois nouvelles routes (§1).
- `registre/tests.py` — nouvelles classes de tests (§8).
- Nouveaux templates : `Templates/registre/commercial/renouvellement_form.html`,
  `activer_contrat.html` (écran de confirmation groupée), `resiliation_form.html`.
- `Templates/registre/commercial/accueil.html` et `contrat_detail.html`
  (C1, déjà commités) — ajout des liens/boutons vers ces nouvelles vues
  (« Renouveler », « Activer », « Résilier »), aujourd'hui absents
  puisque les URLs n'existaient pas encore.
- `registre/models.py` — **seulement si l'Option 1 du §2.3 est
  retenue** (règle `clean()` sur `date_debut`, pas de migration).
- `Documentation/00_IA/DECISIONS.md` — déjà mis à jour (arbitrages du
  24/09/2026).

Aucun changement à `registre/permissions.py` ni
`registre/contractualisation.py` (réutilisés tels quels).

---

## 10. Points restant à confirmer avant développement

1. Auto-validation systématique de la `DemandeAvenant` de reprise (§2.2)
   — y compris quand le périmètre est modifié, plutôt que de la laisser
   `EN_ATTENTE` pour un futur écran C4.
2. `date_debut` au 1er du mois pour tout `ContratCommercial` (§2.3,
   Option 1 recommandée) — nouvelle règle métier sur le modèle.
3. Portée exacte de `resiliation_form` par `pk` (§3) — accepter
   d'appeler cette vue sur un contrat qui n'est pas `ACTIF`, ou
   restreindre explicitement ?
4. Niveau de preuve souhaité pour les tests de concurrence (§8.4) —
   vérification de la présence de `select_for_update()` dans les
   requêtes (proposé), ou test multi-thread réel (`TransactionTestCase`,
   nouveau patron pour la suite) ?

---

## Prochaine étape

Confirmation de ces quatre points, puis GO explicite pour le
développement de C2 — dans le respect strict de la méthode déjà
suivie (implémentation, `manage.py check`, tests C2 ciblés, suite
complète, `makemigrations --check --dry-run`, rapport, validation DT,
commit).
