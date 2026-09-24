# P5-L1 — Lot C3 : analyse d'architecture (soumission et liste des demandes d'avenant)

Document d'analyse, préalable à la revue DT, à la proposition
technique C3 et à tout développement. **Aucune modification de
code, aucune migration.** Fait suite au Lot C2 (commit `e090817`,
310/310 tests verts, clos le 24/09/2026).

Base : état réel du code après `e090817` (`models.py`, `permissions.py`,
`contractualisation.py`, `views.py`, `urls.py`, templates
`registre/commercial/`) et l'ensemble des décisions P5-L1 consignées
dans `DECISIONS.md`, notamment l'architecture technique du 19/09/2026
(`2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md`, §1.3
et §4.4) qui a introduit `DemandeAvenant`/`LigneDemandeAvenant` et
conçu en détail l'écran de soumission — largement réutilisée ci-dessous
plutôt que redécidée.

**Rien ci-dessous ne rouvre les arbitrages déjà tranchés** : séparation
stricte `DemandeAvenant` (workflow) / `MouvementPerimetre` (source de
vérité, jamais créé directement) — Lot A ; droit opérationnel ≠ pouvoir
contractuel — arbitrage point 6 ; patron de refus par redirection,
jamais `Http404`, pour les contrôles de gestion commerciale — Lot B ;
`commercial_gestion_requis`/`verifier_acces_gestion_contrat`/
`gestion_contrat_autorisee`/`demandes_avenant_visibles` — Lot B,
inchangés depuis. Seules les questions propres à la soumission et à la
consultation des demandes sont posées.

---

## 1. Ce qui est déjà acquis — soumission et consultation (architecture §1.3/§4.4, 19/09/2026)

Ce paragraphe est un rappel, pas une nouvelle proposition : ces points
ont déjà été validés par Phil le 19-21/09/2026, avant même le Lot A.
Ils répondent directement aux points 1, 2, 3 et 4 de la consigne.

- **Qui peut soumettre** : « Tout demandeur
  (admin/responsable_securite/gestionnaire_contractuel/directeur) »,
  même droit que `nouveau_etablissement` — c'est-à-dire
  `gestionnaire_requis` (vérifié dans `permissions.py`, inchangé
  depuis Phase 4), pas une nouvelle primitive.
- **Qui peut valider/rejeter** : `admin`/`responsable_securite`/
  `gestionnaire_contractuel` **du contrat actif** — exactement
  `verifier_acces_gestion_contrat(user, contrat)`, déjà écrite au Lot B
  avec cette DemandeAvenant explicitement citée dans sa docstring comme
  cas d'usage prévu.
- **Comportement par rôle, déjà tranché** :
  - Tout demandeur voit le même écran de soumission (prévisualisation
    d'impact, §4.4 ci-dessous).
  - Si le demandeur a aussi les droits de validation (admin,
    responsable_securite, ou gestionnaire_contractuel du contrat
    actif) : peut valider sa propre demande dans la foulée — « pas de
    raccourci qui contourne l'objet » : la `DemandeAvenant` existe
    toujours, même pour ce cas, pour que l'audit reste uniforme quel
    que soit qui a agi.
  - Si le demandeur n'a pas les droits de validation (**cas exact du
    point 1 de la consigne : un directeur non gestionnaire**) : la
    demande reste `EN_ATTENTE`, visible dans la liste des demandes en
    attente pour les rôles habilités — **aucune validation automatique,
    aucune notification** (décision explicite, hors périmètre de
    P5-L1).
- **Consultation (liste)** : `demandes_avenant_visibles(user)` (Lot B)
  couvre déjà exactement la matrice attendue — admin/responsable_securite/
  superuser : toutes ; gestionnaire_contractuel : toutes celles de son
  contrat (y compris hors de son périmètre opérationnel, arbitrage Lot
  B) ; directeur non gestionnaire : celles touchant son périmètre
  opérationnel (`etablissements_autorises`) uniquement. **Aucune
  fonction nouvelle à écrire pour la liste** (point 8 de la consigne).
- **Écran de prévisualisation d'impact (point 5 de la consigne)** :
  entièrement conçu en architecture §4.4, texte exact déjà rédigé par
  Phil :
  ```
  Modification du périmètre contractuel
  Vous ajoutez : 1 établissement, 2 bâtiments
  Impact tarifaire
    Abonnement actuel : 159 € HT/mois
    Nouveau montant : 203 € HT/mois
    Évolution : +44 € HT/mois
  La modification prendra effet le 1er du mois suivant.
  Un avenant à votre contrat sera nécessaire.
  [Annuler]  [Soumettre la demande]
  ```
  Calcul « avant/après » : **simulation pure, sans écriture en base** —
  réutilise `perimetre_a_date`/`tarif_mensuel` (C0, inchangées depuis),
  en y ajoutant temporairement les lignes candidates. Aucune nouvelle
  fonction de calcul à écrire — confirme le point 5 de la consigne.
- **Le message préventif cité dans la consigne** (« Attention un
  avenant à votre contrat va être généré ! ») **correspond exactement**
  à cet écran déjà conçu — ce n'est pas un message ponctuel
  supplémentaire à ajouter ailleurs, c'est l'écran de soumission
  lui-même. Répond au point 4 de la consigne : il **remplace** l'idée
  d'un simple message d'avertissement, plutôt qu'il ne s'y ajoute —
  décision déjà actée le 19/09/2026 (« ni simple message, ni
  pré-validation bloquante — un workflow de demande »).

## 2. Modèles vérifiés dans le code réel après `e090817` (point 7 de la consigne)

Vérification directe (pas une supposition) de `registre/models.py`,
inchangé sur ces points depuis le Lot A (le Lot C2 n'a touché que
`ContratCommercial.clean()`) :

- **`DemandeAvenant`** : `contrat_commercial` (FK `PROTECT`,
  `related_name='demandes'`), `demandeur` (FK `PROTECT`), `date_demande`
  (auto), `statut` (`EN_ATTENTE`/`VALIDEE`/`REJETEE`, trois valeurs
  seulement), `validateur` (FK `SET_NULL`, nullable), `date_traitement`
  (nullable), `commentaire_validation`, `date_effet_souhaitee`
  (`clean()` exige le 1er du mois — déjà vérifié et réutilisé sans
  modification au Lot C2).
- **`LigneDemandeAvenant`** : `demande` (FK `CASCADE`,
  `related_name='lignes'`), `type_mouvement` (`AJOUT`/`RETRAIT`),
  `type_objet` (`ETABLISSEMENT`/`BATIMENT`), `etablissement`/`batiment`
  (FK `PROTECT`, nullables, exclusivité vérifiée par `clean()`).
  **Aucun champ de quantité, aucun champ tarif** — une ligne = un objet.
- **`MouvementPerimetre`** : `ligne_demande_origine` est un
  **`OneToOneField` vers `LigneDemandeAvenant`, non nul**
  (`on_delete=PROTECT`) — confirmation directe dans le code (pas une
  supposition) qu'**aucun `MouvementPerimetre` ne peut exister sans une
  `LigneDemandeAvenant` d'origine**. C'est cette contrainte structurelle,
  pas une simple convention, qui garantit le point 6 de la consigne
  (jamais d'écriture directe dans `MouvementPerimetre`).
- **`ContratCommercial`** : `demandes` (related_name, reverse de
  `DemandeAvenant.contrat_commercial`) et `mouvements` (reverse de
  `MouvementPerimetre.contrat_commercial`) — les deux déjà utilisables
  pour un futur affichage (ex. compter les demandes en attente d'un
  contrat), sans aucun champ ni méthode supplémentaire nécessaire.
- **Rien dans le modèle n'empêche** : deux `DemandeAvenant`
  `EN_ATTENTE` simultanées sur le même établissement/contrat (doublon,
  point 10 de la consigne) ; une `DemandeAvenant` sur un contrat qui
  n'est plus `ACTIF` (`contrat_commercial` n'est jamais revalidé après
  création) ; une `DemandeAvenant` à zéro ligne. Ces trois points sont
  donc à traiter en vue/formulaire, pas déjà couverts par le modèle —
  voir §6.

## 3. Permissions déjà développées, réutilisées telles quelles (point 8 de la consigne)

Aucune primitive nouvelle proposée. Celles du Lot B couvrent
intégralement le besoin :

| Besoin | Primitive existante | Origine |
|---|---|---|
| Autoriser la soumission | `gestionnaire_requis` | Phase 4, inchangé |
| Scoper la liste par rôle | `demandes_avenant_visibles(user)` | Lot B |
| Autoriser la validation/rejet d'une demande précise | `verifier_acces_gestion_contrat(user, demande.contrat_commercial)` | Lot B |
| Restreindre les établissements sélectionnables par un directeur | `etablissements_autorises(user)` | Pré-existant (IDOR, Phase 1/4) |

Le dernier point (restreindre les établissements sélectionnables) n'a
**jamais été appliqué à une `DemandeAvenant`** jusqu'ici — c'est une
**application nouvelle** d'une primitive existante, pas une primitive
nouvelle. Voir §5 pour le détail.

## 4. Conventions C1/C2 à reprendre (point 9 de la consigne)

- Préfixe de routes `/commercial/...`, déjà établi.
- `/commercial/demandes/` → `demande_avenant_liste`, déjà nommée dans
  la proposition technique Lot C initiale (whole-lot), réutilisant
  `demandes_avenant_visibles` sans changement.
- Décorateur de vue + vérification objet en deux temps (ex.
  `resiliation_form` au Lot C2) : `@gestionnaire_requis` en entrée,
  puis `verifier_acces_gestion_contrat` pour la validation/rejet d'une
  demande précise — même patron.
- Templates : sous-dossier `Templates/registre/commercial/`,
  `atable-wrap`/`atable` pour les listes (`contrat_historique.html`),
  `form-card`/`form-group` pour les formulaires
  (`renouvellement_form.html`).
- Champs à cocher établissements/bâtiments : patron déjà écrit au Lot
  C2 (`renouvellement_form.html`, périmètre pré-coché avec
  établissements/bâtiments `actif=True`) — directement réutilisable
  pour `demande_avenant_form`.
- Transaction + `messages` en import local dans la vue : patron
  systématique depuis C0/C1/C2.

## 5. Point d'entrée de la soumission — ambiguïté à trancher

**C'est le point le plus structurant de cette analyse, et il n'est pas
tranché par l'architecture technique.**

L'architecture §4.4 est rédigée entièrement autour de la **création
d'un établissement** (« Interaction avec la création d'un
établissement ») — elle décrit l'écran de soumission comme s'il
s'enchaînait juste après `nouveau_etablissement`. Mais vérification
faite du code réel : `nouveau_etablissement` et `nouveau_batiment`
(`views.py`, lignes 804-882) sont aujourd'hui des vues **directes,
sans aucune étape intermédiaire** — création immédiate, redirection
immédiate vers `detail_etablissement`. Aucun hook, aucun signal,
aucune interruption de ce parcours n'existe.

Or le modèle admet aussi des demandes qui **ne sont liées à aucune
création** : un `RETRAIT` (établissement ou bâtiment qui sort du
périmètre contractuel sans être supprimé ni archivé), ou un `AJOUT`
d'un établissement **déjà existant** qui n'a jamais été intégré au
périmètre contractuel (cas d'un établissement créé avant P5-L1, ou
créé sans qu'un avenant ait suivi). Ces cas n'ont **aucun événement de
création** auquel s'accrocher.

Deux lectures possibles, non tranchées :

- **Option A — formulaire autonome.** `demande_avenant_form` est une
  vue à part entière, atteignable depuis `commercial_accueil`,
  `contrat_detail`, ou la fiche d'un établissement
  (`detail_etablissement`), permettant de choisir librement des
  établissements/bâtiments en `AJOUT` **ou** `RETRAIT`, sans lien
  direct avec un acte de création. `nouveau_etablissement`/
  `nouveau_batiment` restent **strictement inchangés** — aucun risque
  sur ces vues très utilisées, aucun élargissement du périmètre de
  fichiers touchés en dehors du module commercial.
- **Option B — hook intégré.** `nouveau_etablissement`/
  `nouveau_batiment` sont modifiés pour proposer, immédiatement après
  la création, l'écran de soumission décrit en §1 (le parcours que
  l'architecture §4.4 semble décrire littéralement). Nécessite de
  toucher deux vues opérationnelles historiques (Phase 4), en dehors
  du module commercial strict — et ne couvre de toute façon pas les
  retraits ni les établissements déjà existants, qui resteraient
  couverts par un formulaire autonome en complément.

**Recommandation de cette analyse : Option A seule (formulaire
autonome), sans modifier `nouveau_etablissement`/`nouveau_batiment`.**
Elle couvre tous les cas (ajout après création, ajout d'un existant,
retrait) avec un seul mécanisme, respecte la discipline déjà en place
de ne pas mélanger le module commercial avec les vues opérationnelles
historiques (arbitrage point 6 — séparation stricte), et n'élargit pas
le périmètre de fichiers modifiés. **Mais ceci reste une
recommandation, pas une décision** : à confirmer explicitement, car la
consigne du 19/09/2026 est littéralement écrite autour de la création
d'établissement et pourrait avoir sous-entendu l'option B.

## 6. Un directeur non gestionnaire voit-il les montants globaux dans la prévisualisation ? — contradiction à signaler

**Contradiction directe entre deux décisions déjà actées, jamais
confrontées l'une à l'autre avant ce lot.**

- Architecture §4.4 (19/09/2026) : « **Tout demandeur**
  (admin/responsable_securite/gestionnaire_contractuel/**directeur**) »
  voit l'écran de soumission, avec les montants **« Abonnement actuel :
  159 € HT/mois » / « Nouveau montant : 203 € HT/mois »** — des
  montants **globaux**, portant sur l'ensemble du contrat.
- Architecture §4.1 (également 19/09/2026, opérationnalisée et testée
  au Lot C1) : les **agrégats sur l'ensemble du périmètre** (montant
  mensuel total de l'instance) sont **réservés à
  admin/responsable_securite** (et au gestionnaire_contractuel, via
  l'arbitrage C1 du 21/09/2026) — un directeur non gestionnaire ne voit
  **jamais** le montant total du contrat, seulement sa propre part
  (`contrat_detail`, déjà développé et testé : `ma_part_facture`, pas
  `montant_mensuel`).

Si l'écran de soumission de §4.4 est implémenté littéralement (montants
avant/après **globaux** pour tout demandeur, y compris un directeur non
gestionnaire), il **contredit directement** la restriction déjà
développée et testée au Lot C1. Deux résolutions possibles, non
tranchées :

- **Conserver les montants globaux pour tout demandeur** (lecture
  littérale de §4.4) : justifiable par le fait que c'est une
  **prévisualisation transitoire** de l'effet de sa propre action, pas
  une consultation permanente du contrat — mais crée une divergence
  entre ce qu'un directeur voit ponctuellement (montant total) et ce
  qu'il voit en consultation habituelle (sa part seulement).
- **Scoper l'impact affiché à un directeur non gestionnaire** à sa
  seule part (établissements ajoutés/retirés et leur coût, sans le
  total ni l'« abonnement actuel » global) — cohérent avec la
  restriction déjà en place, mais un écart avec le texte exact rédigé
  par Phil en §4.4.

**Signalé explicitement, non tranché.**

## 7. Cas d'erreur (point 10 de la consigne) — état des lieux

| Cas | Couvert par le modèle ? | À traiter en vue |
|---|---|---|
| Contrat inexistant | — | `get_object_or_404` classique |
| Contrat non `ACTIF` | Non — `contrat_commercial` accepte n'importe quel statut | **À trancher** : soumission possible seulement contre le contrat `ACTIF` courant ? Redirection vers `commercial_accueil` si aucun (cohérent avec le patron déjà retenu C1) |
| Demande déjà validée/rejetée | Non — rien n'empêche une deuxième action sur une demande déjà traitée | **À construire** (C4, pas C3) : vérifier `statut == 'EN_ATTENTE'` avant toute action de validation/rejet, même patron que `activer_contrat` (Lot C2) sur un contrat déjà activé |
| Établissement hors périmètre autorisé | Non — `LigneDemandeAvenant` n'a aucune vérification de périmètre | **À trancher** : un directeur non gestionnaire doit-il être restreint à `etablissements_autorises(user)` dans le formulaire de soumission (cohérent avec `modifier_etablissement`, IDOR) ? Recommandation : oui — mais jamais appliqué à cet objet jusqu'ici, à confirmer explicitement |
| Bâtiment incohérent (établissement+bâtiment tous deux renseignés, ou aucun) | **Oui** — `LigneDemandeAvenant.clean()`, déjà en place, réutilisé sans modification | — |
| Demande vide (zéro ligne) | Non — le modèle n'impose aucun minimum | **À construire** : validation de formulaire, au moins une ligne requise |
| Doublon (deux demandes `EN_ATTENTE` sur le même établissement) | Non — aucune contrainte, ni applicative ni SQL | **Signalé, non tranché** : bloquer, avertir, ou laisser faire (une validation ultérieure resterait sans effet néfaste, `perimetre_a_date` traite un ensemble, pas un compteur — un double `AJOUT` ne casse rien techniquement, mais reste une donnée confuse) |
| Demande concernant un contrat qui n'est plus le contrat actif | Non — `contrat_commercial` est figé à la création, jamais revalidé | **Nouveau cas, apparu avec le Lot C2** : une demande `EN_ATTENTE` peut survivre au renouvellement de son contrat (l'ancien passe `EXPIRE`). Faut-il l'empêcher (interdire la validation d'une demande dont le contrat n'est plus `ACTIF`), l'autoriser explicitement (un avenant sur un contrat expiré n'a plus de sens), ou la signaler ? **Signalé, non tranché** — interaction directe C2 × C3 |

## 8. Historisation (point 11 de la consigne)

- Une demande `REJETEE` **ne doit jamais** produire de
  `MouvementPerimetre` — déjà garanti structurellement par
  l'`OneToOneField` non nul (§2) : un `MouvementPerimetre` ne peut
  exister qu'en résultat d'une validation qui le crée explicitement,
  jamais d'un rejet.
- Une demande `VALIDEE` doit permettre de retrouver le/les
  `MouvementPerimetre` correspondants : déjà possible sans rien ajouter
  — `ligne.mouvement` (accesseur inverse du `OneToOneField`,
  `related_name='mouvement'`) pour chaque `LigneDemandeAvenant` de la
  demande. **Aucun champ ni méthode supplémentaire nécessaire** sur
  `DemandeAvenant` : la liste peut itérer `demande.lignes.all()` et
  afficher `ligne.mouvement` s'il existe.
- Aucune suppression, aucune modification destructive à aucune étape —
  cohérent avec tout le reste de P5-L1.

## 9. Découpage proposé de C3 (point demandé en conclusion)

La proposition technique Lot C initiale (whole-lot, non individuellement
validée mais jamais contredite) séparait déjà :

- **C3** : `demande_avenant_form` (soumission) + `demande_avenant_liste`
  (consultation, lecture seule — y compris l'affichage des statuts
  `VALIDEE`/`REJETEE` déjà traités et de leurs `MouvementPerimetre`
  liés, mais **sans aucune action d'écriture** sur une demande
  existante).
- **C4** : `demande_avenant_validation` (l'action de valider/rejeter
  elle-même — la transaction qui crée les `MouvementPerimetre`).

**Je comprends que ce découpage reste valide** pour C3 : la consigne
actuelle mentionne les trois statuts et le lien vers
`MouvementPerimetre`, mais uniquement comme ce que la **liste doit
afficher** (lecture), pas comme une action à coder dans ce lot — à
confirmer, car les points 1 à 3 de la consigne évoquent aussi le
comportement de validation, qui pourrait être lu comme relevant déjà
de C3.

## 10. Fichiers qui seraient concernés (développement futur, aucune modification maintenant)

- `registre/forms.py` — nouveau `DemandeAvenantForm` (+ gestion des
  lignes dynamiques, formset ou équivalent, pas un enjeu
  d'architecture).
- `registre/views.py` — nouvelles vues `demande_avenant_form`,
  `demande_avenant_liste`.
- `registre/urls.py` — 2 nouvelles routes (`/commercial/demandes/`,
  et l'URL de soumission selon l'option retenue au §5).
- `registre/tests.py` — nouvelles classes de tests (§11).
- Nouveaux templates `Templates/registre/commercial/demande_avenant_form.html`,
  `demande_avenant_liste.html`.
- `Templates/registre/commercial/accueil.html`/`contrat_detail.html` —
  éventuel lien vers la liste des demandes (à l'image des boutons
  ajoutés au Lot C2).
- **Si l'Option B est retenue au §5** : `registre/views.py`
  (`nouveau_etablissement`, `nouveau_batiment`) et leurs templates —
  périmètre nettement plus large, à valider explicitement avant tout
  développement.

Aucun changement à `registre/models.py`, `registre/permissions.py`,
`registre/contractualisation.py` (tous réutilisés tels quels).

## 11. Stratégie de tests proposée (point 12 de la consigne)

- **Matrice des rôles (soumission)** : admin/responsable_securite/
  gestionnaire_contractuel/directeur autorisés (tous, `gestionnaire_requis`) ;
  factotum/prestataire refusés.
- **Matrice des rôles (consultation)** : reprise directe des tests
  `DemandesAvenantVisiblesTests` (Lot B, déjà verts) — pas de nouveaux
  cas de fond, seulement vérifier que la vue `demande_avenant_liste`
  restitue exactement ce que retourne `demandes_avenant_visibles`.
- **Création** : ligne(s) correctement rattachée(s) à la demande ;
  `statut` toujours `EN_ATTENTE` à la création, jamais autre chose ;
  `demandeur` = utilisateur courant.
- **Impact établissement / impact bâtiment** : la prévisualisation
  (avant soumission) reflète exactement `perimetre_a_date`/
  `tarif_mensuel` recalculés avec les lignes candidates ajoutées, sans
  écriture en base tant que le formulaire n'est pas soumis.
- **Absence de modification du périmètre avant validation** : après
  soumission d'une `DemandeAvenant` (statut `EN_ATTENTE`),
  `perimetre_a_date`/`tarif_mensuel` du contrat sont **strictement
  inchangés** — test explicite, cœur du point 6 de la consigne.
- **Aucun `MouvementPerimetre` créé à la soumission** : compter
  `MouvementPerimetre.objects.count()` avant/après, doit être
  strictement identique.
- **Cas d'erreur** (§7) : contrat non `ACTIF`, demande vide,
  établissement hors périmètre autorisé pour un directeur, bâtiment
  incohérent (déjà couvert par `LigneDemandeAvenant.clean()`, à
  vérifier via la vue).
- **Historisation** : `demande.lignes.all()` et (une fois C4 construit)
  `ligne.mouvement` restent accessibles et cohérents — pour C3, se
  limite à vérifier que la structure de lecture fonctionne sur des
  demandes déjà validées/rejetées créées directement en fixture de
  test (sans passer par une vue de validation qui n'existe pas encore).

---

## Décisions déjà acquises (résumé)

Qui peut soumettre (tout rôle via `gestionnaire_requis`) ; qui peut
valider/rejeter (`verifier_acces_gestion_contrat`) ; comportement par
rôle (auto-validation si droits, sinon `EN_ATTENTE` visible en liste,
jamais de notification) ; contenu exact de l'écran de prévisualisation
pour l'ajout ; réutilisation intégrale de `perimetre_a_date`/
`tarif_mensuel` (C0) et de `demandes_avenant_visibles` (Lot B) ; aucune
primitive de permission nouvelle ; `MouvementPerimetre` structurellement
impossible à créer hors validation d'une `DemandeAvenant`
(`OneToOneField` non nul, vérifié dans le code).

## Points fonctionnels à arbitrer

1. **Point d'entrée de la soumission** (§5) : formulaire autonome
   (recommandé) ou hook intégré à `nouveau_etablissement`/
   `nouveau_batiment` ?
2. **Montants globaux dans la prévisualisation pour un directeur non
   gestionnaire** (§6) : contradiction entre architecture §4.4 (« tout
   demandeur » voit les montants globaux) et la restriction déjà
   développée au Lot C1 (agrégats réservés à admin/responsable/
   gestionnaire). Conserver tel quel, ou scoper l'aperçu ?
3. **Restriction des établissements sélectionnables** pour un
   directeur non gestionnaire (§7) : appliquer `etablissements_autorises`
   au formulaire de soumission ?
4. **Doublons** (§7) : bloquer, avertir, ou laisser deux demandes
   `EN_ATTENTE` coexister sur le même établissement ?
5. **Demande orpheline après renouvellement** (§7) : une
   `DemandeAvenant` `EN_ATTENTE` dont le contrat est devenu `EXPIRE`
   entre-temps (nouveauté du Lot C2) — bloquer sa validation, ou
   signaler seulement ?
6. **Découpage C3/C4** (§9) : confirmation que C3 se limite à
   soumission + consultation (lecture), la validation/rejet restant C4.

## Découpage proposé

C3 = `demande_avenant_form` (soumission) + `demande_avenant_liste`
(consultation). C4 = `demande_avenant_validation` (action).

## Fichiers concernés (développement futur)

Voir §10.

## Stratégie de tests proposée

Voir §11.

---

Attente de l'arbitrage DT sur les six points ci-dessus avant toute
proposition technique C3.
