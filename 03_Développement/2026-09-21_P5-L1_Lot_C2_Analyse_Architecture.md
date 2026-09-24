# P5-L1 — Lot C2 : analyse d'architecture (renouvellement / nouveau contrat / activation)

Document d'analyse, préalable à la revue DT, à la proposition
technique C2 et à tout développement. **Aucune modification de
code.** Fait suite au Lot C1 (commit `1173a6c`, 279/279 tests verts,
clos le 21/09/2026).

Portée strictement C2, telle que cadrée par la consigne : création
d'un nouveau `ContratCommercial`, renouvellement, `activer_contrat`,
contrôles métier, permissions, historisation, tests. `DemandeAvenant`
(soumission/liste, C3) et sa validation/rejet (C4) restent hors
périmètre.

**Rien ci-dessous ne rouvre les arbitrages déjà tranchés** : C0
préalable (acquis, commité) ; séquence de renouvellement explicite,
jamais de bascule automatique silencieuse (architecture technique
§5, proposition Lot C §3) ; matrice de consultation C1 (acquise,
commitée) ; routes sous `/commercial/...` ; historisation par
nouvelle ligne jamais par modification (Lot A). Seules des questions
propres à la création/au renouvellement/à l'activation sont posées.

Consigne explicite de Phil respectée : cette analyse **commence**
par la vérification de l'implémentation actuelle de la contrainte
d'unicité `ACTIF`, avant tout le reste — c'est elle qui conditionne
la conception de la bascule atomique.

---

## 1. Contrainte d'unicité `ACTIF` — implémentation actuelle vérifiée

**Vérifié dans le code réel** (`registre/models.py`, lignes
1597-1622, et migration `0024_contratcommercial_...py`) :

- La règle « un seul contrat `ACTIF` à la fois » est appliquée
  **uniquement au niveau applicatif**, dans
  `ContratCommercial.clean()` :
  ```python
  if self.statut == 'ACTIF':
      autres_actifs = ContratCommercial.objects.filter(statut='ACTIF')
      if self.pk:
          autres_actifs = autres_actifs.exclude(pk=self.pk)
      if autres_actifs.exists():
          raise ValidationError(...)
  ```
  `clean()` est appelé par `full_clean()`, lui-même appelé
  explicitement dans `save()` (ligne 1621) — donc à chaque
  enregistrement passant par l'ORM normal.
- **Aucune contrainte au niveau base de données** : la migration
  0024 ne déclare aucun `UniqueConstraint`/index partiel sur
  `(statut='ACTIF')`, et `ContratCommercial.Meta` n'en porte aucun.
  Vérifié par relecture complète du modèle et de la migration.

**Conséquences techniques, à noter pour la conception de C2** :

1. La garde ne protège que le chemin `Model.save()`. Un
   `QuerySet.update()` ou un `bulk_create()`/`bulk_update()`
   contournerait silencieusement la règle. Aucun code existant ne le
   fait aujourd'hui pour `ContratCommercial` — à respecter comme
   contrainte de conception pour C2 (toujours `.save()`, jamais
   `.update()` sur le statut).
2. **Risque de concurrence théorique** : deux requêtes simultanées
   pourraient toutes deux lire « aucun `ACTIF` » avant que l'une des
   deux ne committe, et passer `clean()` toutes les deux. Aucun
   verrouillage (`select_for_update`) n'existe nulle part ailleurs
   dans le code PSM2S actuel (vérifié par recherche globale : seul
   `transaction.atomic()` est utilisé, jamais de verrou de ligne).
   Compte tenu du profil d'usage (une poignée d'`admin`/
   `responsable_securite`, action manuelle et peu fréquente), le
   risque réel est faible — mais c'est une simplification délibérée
   à signaler, pas un point réglé implicitement (§9, point 5).
3. **Ordre des écritures pour la bascule atomique** : parce que
   `clean()` interroge l'état de la base au moment du `save()`, et
   que les écritures propres à une transaction en cours sont
   visibles à ses requêtes suivantes (sémantique transactionnelle
   standard), la séquence suivante fonctionne à l'intérieur d'un
   seul `transaction.atomic()` :
   1. `ancien.statut = 'EXPIRE'` ; `ancien.save()`
   2. `nouveau.statut = 'ACTIF'` ; `nouveau.save()`

   Si l'étape 2 échoue (`ValidationError` pour toute raison), la
   transaction entière est annulée — l'étape 1 ne persiste jamais
   seule. **L'ordre inverse ne fonctionnerait pas** : activer le
   nouveau contrat avant de rétrograder l'ancien ferait échouer
   `clean()` immédiatement, puisque l'ancien contrat est encore
   `ACTIF` au moment de la vérification.

   Cette séquence, combinée à `transaction.atomic()` (déjà un
   patron établi dans `views.py`, ex. lignes 2487, 2574, 2839),
   suffit à garantir qu'**aucun état intermédiaire ne persiste
   jamais en base** — sans mécanisme supplémentaire. C'est la
   réponse technique à la question posée par la consigne.

---

## 2. Rappel de ce qui est déjà acquis (sources, pas de nouvelle décision)

- **Modèle** : `ContratCommercial.STATUT_CHOICES` =
  `EN_ATTENTE`/`ACTIF`/`RESILIE`/`EXPIRE` ; `duree_engagement_mois`
  déjà contraint à 24/36/48 par `choices` ; `date_fin` toujours
  calculée (`_ajouter_mois`), jamais saisie ; `contrat_precedent`
  (FK vers `self`, `PROTECT`, `related_name='renouvellements'`) déjà
  en place et jamais utilisé par aucune vue à ce jour.
- **Permissions** (Lot B, commit `31a0fdf`) : `commercial_gestion_requis`
  (admin/responsable_securite seuls) — sa docstring anticipe
  **déjà explicitement** le cas d'usage du renouvellement : « réservé
  aux actions de gestion commerciale qui ne dépendent pas d'un
  contrat précis déjà résolu (ex. renouvellement, qui exige une
  réassignation explicite du gestionnaire_contractuel — toujours par
  admin/responsable_securite) ». `verifier_acces_gestion_contrat`
  cite elle-même la résiliation comme cas d'usage prévu.
- **Architecture technique §4.2** (validée 19/09/2026) : au
  renouvellement, `gestionnaire_contractuel` est pré-rempli depuis le
  contrat précédent, mais la validation est **explicite et
  obligatoire** — le champ reste visible et doit être soumis
  consciemment, jamais de reconduction silencieuse.
- **Proposition technique Lot C** (whole-lot, non re-validée ligne à
  ligne mais seule source existante sur C2) situait déjà
  `renouvellement_form`, `activer_contrat` et `resiliation_form`
  ensemble dans ce sous-lot, et avait recommandé — sans trancher —
  l'**Option A** pour `activer_contrat` (un seul écran de
  confirmation nommant explicitement les deux effets avant tout
  enregistrement, une seule action produisant les deux écritures),
  face à l'Option B (deux gestes séparés, activation refusée tant que
  l'ancien contrat n'est pas déjà clos).

---

## 3. Point 1 — Création d'un nouveau `ContratCommercial`

- Créé **toujours** avec `statut='EN_ATTENTE'` — jamais directement
  `ACTIF`, ce que `clean()` interdirait de toute façon tant qu'un
  autre contrat est `ACTIF` (cas normal). Aucune branche de code
  spéciale à écrire pour l'empêcher : le modèle le fait déjà.
- `contrat_precedent` = contrat `ACTIF` courant s'il existe, sinon
  `None` — le modèle accepte déjà `null=True, blank=True`, donc le
  tout premier contrat de l'instance n'est pas un cas particulier à
  coder.
- `duree_engagement_mois` : simple exposition du champ `ModelForm`,
  déjà contraint par `choices`.
- `gestionnaire_contractuel` : pré-rempli en valeur initiale du
  formulaire depuis `contrat_precedent.gestionnaire_contractuel`,
  champ requis et modifiable, jamais rempli hors soumission
  explicite (architecture §4.2, déjà validée).
- `date_debut`, tarifs, maintenance : saisie explicite — voir §6
  (contrôles métier) pour les points encore ouverts.

## 4. Point 2 — Renouvellement (séquence)

- À la création du nouveau contrat, **l'ancien contrat n'est touché
  en aucune façon** — aucune écriture sur son statut ni sur aucun de
  ses champs. Un `ACTIF` et un `EN_ATTENTE` coexistant n'est pas un
  état incohérent : c'est un état déjà prévu par
  `STATUT_CHOICES`, et la contrainte d'unicité ne porte que sur
  `ACTIF`.
- La contrainte « un seul `ACTIF` » est donc respectée **par
  construction** dès la création : rien ne change côté ancien
  contrat tant que `activer_contrat` n'est pas explicitement
  déclenché. Aucun état incohérent durable n'est possible entre la
  création et l'activation, quelle que soit sa durée.

## 5. Point 3 — `activer_contrat`

- Vue dédiée, écriture (POST), `commercial_gestion_requis`
  (admin/responsable_securite seuls, cf. §2).
- **Geste de confirmation groupé** : compris ici comme l'Option A de
  la proposition technique Lot C — un écran nomme explicitement les
  deux effets (« ce contrat va passer à Actif, le contrat en cours
  [dates] va passer à Expiré ») avant tout enregistrement, une seule
  soumission produit les deux écritures. Cette lecture est cohérente
  avec la consigne (« geste de confirmation groupé »), mais **cet
  arbitrage Option A vs B n'a jamais été consigné dans
  `DECISIONS.md`** — seulement recommandé dans la proposition Lot C.
  Comme pour les arbitrages C1, je propose de l'y ajouter formellement
  avant/avec la proposition technique C2 (§9, point 6).
- **Séquence atomique** : cf. §1 — `EXPIRE` de l'ancien puis `ACTIF`
  du nouveau, dans un seul `transaction.atomic()`.
- **Cas du tout premier contrat** (`contrat_precedent=None`) : rien à
  basculer côté ancien, l'écran de confirmation ne porte que sur
  l'activation elle-même — déjà anticipé par la proposition Lot C.
- **Aucun mécanisme automatique** (cron, tâche planifiée) à la date
  de fin naturelle d'un contrat — déjà tranché (proposition Lot C
  §3) : le contrat reste `ACTIF` en base jusqu'à action explicite,
  `statut_coherent` (C0) signale l'écart sans jamais corriger.

## 6. Point 4 — Contrôles métier

- **Durée** : déjà garantie par `choices` (24/36/48) — rien à
  ajouter.
- **Cohérence du statut** : déjà couverte par `ContratCommercial.clean()`
  (un seul `ACTIF`) + `statut_coherent` (C0, signal a posteriori,
  réutilisable tel quel) — pas de nouvelle règle nécessaire pour C2.
- **Gestionnaire contractuel** : couvert au §3/§4.2.
- **Dates** : le modèle n'impose aujourd'hui **aucune** relation entre
  `date_fin` de l'ancien contrat et `date_debut` du nouveau (ni
  continuité obligatoire, ni interdiction de chevauchement). Point
  ouvert — voir §9, point 4.
- **Périmètre** : le modèle ne prévoit **aucune recopie automatique**
  des `MouvementPerimetre` de l'ancien contrat vers le nouveau (`FK`
  `contrat_commercial` propre à chaque contrat). Point majeur, pas un
  détail — voir §9, point 2.
- **Tarif** : la consigne demande un pré-remplissage explicite pour le
  gestionnaire, mais ne dit rien des tarifs. Point ouvert — voir §9,
  point 3.

## 7. Point 5 — Permissions

| Action | `admin`/`responsable_securite` | Gestionnaire du contrat | Directeur non gestionnaire | Autres rôles |
|---|---|---|---|---|
| Créer un nouveau contrat (renouvellement) | Oui (`commercial_gestion_requis`) | Non | Non | Non |
| Activer un contrat (`activer_contrat`) | Oui (`commercial_gestion_requis`) | Non | Non | Non |
| Consulter le nouveau contrat une fois créé | Oui | Oui, si désigné dessus (`gestion_contrat_autorisee`, C1) | Limité (C1, §4.1) | Non |

Le gestionnaire du contrat **ne peut pas** créer/renouveler/activer :
ce sont des actions « qui ne dépendent pas d'un contrat précis déjà
résolu » (au moment de la création, il n'existe pas encore d'objet
contre lequel vérifier `gestion_contrat_autorisee`) — exactement la
distinction déjà écrite dans la docstring de
`commercial_gestion_requis` (Lot B). Ceci respecte strictement les
primitives du Lot B, sans qu'aucune nouvelle fonction de permission
ne soit nécessaire pour C2.

Si la résiliation entre dans le périmètre de C2 (§9, point 1) :
`verifier_acces_gestion_contrat` s'applique (admin/responsable_securite
+ gestionnaire du contrat concerné), cohérent avec sa docstring qui
cite explicitement la résiliation comme cas d'usage prévu.

## 8. Point 6 — Historisation

- Aucune écriture sur l'ancien contrat à la création du nouveau
  (§4). À l'activation, seul son `statut` passe à `EXPIRE` — aucun
  autre champ n'est modifié (dates, tarifs, gestionnaire de l'ancien
  contrat restent intacts pour toujours, conforme au principe déjà
  acté au Lot A : « jamais de modification d'une ligne existante »).
- `contrat_precedent`/`renouvellements` (déjà en place, Lot A) assure
  la traçabilité de la succession — rien à ajouter au modèle.
- Aucune suppression, jamais — cohérent avec tout le reste de P5-L1.

## 9. Ambiguïtés et points non tranchés (signalés, pas résolus)

1. **Résiliation dans le périmètre de C2 ?** La consigne actuelle de
   C2 ne mentionne aucune vue de résiliation, alors que le découpage
   initial (proposition technique Lot C, §6) plaçait
   `resiliation_form` dans C2 aux côtés de `renouvellement_form`/
   `activer_contrat`. À confirmer : résiliation manuelle incluse dans
   ce sous-lot, ou reportée à un sous-lot ultérieur ?
2. **Reprise du périmètre au renouvellement.** Le nouveau contrat
   démarre-t-il avec un périmètre vide (aucune recopie automatique
   des `MouvementPerimetre` de l'ancien contrat, périmètre à
   reconstituer via de nouvelles `DemandeAvenant` après activation,
   C3) ? Ou une recopie automatique du périmètre en vigueur est-elle
   attendue au moment de l'activation ? Rien dans le modèle actuel ne
   prévoit de recopie — à trancher explicitement avant développement,
   ce n'est pas un détail d'ergonomie.
3. **Pré-remplissage des tarifs au renouvellement.** La consigne
   mentionne explicitement le pré-remplissage du gestionnaire, pas
   des tarifs (`tarif_etablissement_mensuel`, `tarif_batiment_mensuel`,
   `maintenance_montant_annuel`). Faut-il les pré-remplir aussi
   (avec confirmation explicite, même logique que le gestionnaire),
   ou laisser une saisie neuve à chaque renouvellement ?
4. **Contrainte de date entre ancien et nouveau contrat.** Faut-il
   empêcher ou signaler un chevauchement/trou entre `date_fin` de
   l'ancien et `date_debut` du nouveau, ou laisser cela entièrement
   libre (cohérent avec la philosophie « signal, jamais de blocage »
   déjà retenue pour `statut_coherent`) ?
5. **Verrouillage concurrentiel (`select_for_update`).** Aucun
   précédent dans le code actuel ; risque de concurrence théorique
   mais faible compte tenu du profil d'usage. Accepter le niveau de
   protection actuel (`clean()` + `transaction.atomic()` + ordre des
   écritures, §1), ou l'ajouter pour C2 ?
6. **Option A pour `activer_contrat`** — comprise comme déjà validée
   par la consigne (« geste de confirmation groupé »), mais jamais
   consignée dans `DECISIONS.md` alors que l'Option B y figurait comme
   alternative concurrente dans la proposition Lot C. À ajouter
   formellement avant/avec la proposition technique C2.
7. **Comportement d'`activer_contrat` sur un contrat qui n'est plus
   `EN_ATTENTE`** (déjà `ACTIF`, `EXPIRE` ou `RESILIE`). Bloquer
   explicitement (message d'erreur), ou considérer que ce cas est déjà
   inatteignable depuis l'interface (aucun lien vers `activer_contrat`
   affiché hors de ce contexte) ? À préciser pour les tests « cas
   d'erreur ».

## 10. Point 7 — Tests à prévoir (catégories, pas de code à ce stade)

- **Création** : contrat créé en `EN_ATTENTE` quelle que soit la
  situation ; `contrat_precedent` correctement lié (ou `None` pour le
  premier contrat) ; gestionnaire pré-rempli mais modifiable et requis.
- **Renouvellement** : ancien contrat strictement inchangé après
  création du nouveau (statut, dates, tarifs, gestionnaire identiques
  avant/après) ; coexistence `ACTIF` + `EN_ATTENTE` acceptée.
- **Activation** : bascule complète (ancien → `EXPIRE`, nouveau →
  `ACTIF`) en une transaction ; cas du premier contrat (rien à
  basculer côté ancien).
- **Impossibilité de deux `ACTIF`** : tentative de `save()` direct
  avec `statut='ACTIF'` alors qu'un autre `ACTIF` existe déjà →
  `ValidationError` (test modèle, indépendant des vues).
- **Transaction/atomicité** : si l'écriture du nouveau contrat échoue
  après celle de l'ancien, vérifier que l'ancien **n'est pas resté**
  `EXPIRE` en base (rollback complet) — test spécifique à la bascule
  atomique, le plus important de ce lot.
- **Gestionnaire/permissions** : admin/responsable_securite autorisés
  sur les 2-3 nouvelles vues ; gestionnaire du contrat refusé
  (créer/renouveler/activer) ; directeur refusé ; factotum/prestataire
  bloqués en amont (`commercial_gestion_requis`).
- **Dates** : durée 24/36/48 correctement reflétée dans `date_fin`
  calculée pour le nouveau contrat.
- **Cas d'erreur** : activation d'un contrat qui n'est plus
  `EN_ATTENTE` (§9, point 7) ; création d'un renouvellement sans
  contrat `ACTIF` existant (autorisé, cas premier contrat).

---

## Prochaine étape

Revue DT de cette analyse — arbitrages sur les 7 points du §9 —
puis, seulement après, proposition technique C2 (vues, URLs,
formulaires, tests précis). Aucun développement avant cette
proposition et un GO explicite, conformément à la méthode suivie
depuis le Lot A.
