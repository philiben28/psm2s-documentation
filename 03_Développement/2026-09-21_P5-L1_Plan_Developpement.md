# P5-L1 — Plan de développement
## Contractualisation, tarification, périmètre

Statut : **plan soumis à validation DT — aucun code, aucune migration,
aucun développement engagé.** Fondé sur l'architecture validée le
21/09/2026 (`2026-09-19_P5-L1_Analyse_Architecture_Contractualisation.md`,
`2026-09-19_P5-L1_Architecture_Technique_Contractualisation.md`) et sur
une vérification directe du code actuel (fichiers cités ci-dessous
réellement ouverts, pas supposés). Le correctif indépendant du 21/09/2026
(rattachement à la création d'établissement) est pris comme base — aucun
retour en arrière dessus.

---

## 1. Modèles Django

**Fichier concerné, vérifié** : `registre/models.py` (aucun modèle
`ContratCommercial`/`DemandeAvenant`/`MouvementPerimetre` existant —
recherché sur tout `Code-Source`, aucune collision de nom). Nouvelle
section en fin de fichier, même convention que les sections existantes
(`Etablissement`, `Contrat`, `Prestataire`, `CorrespondantLocal`…).

Quatre modèles, dans l'ordre de dépendance — champs et règles déjà
détaillés en §1.1/§1.2/§1.3 du document d'architecture technique, non
répétés ici :
1. `ContratCommercial`
2. `MouvementPerimetre` (dont le champ `ligne_demande_origine`, ajouté
   lors de la révision `DemandeAvenant`)
3. `DemandeAvenant`
4. `LigneDemandeAvenant`

**Relations avec l'existant** : `ContratCommercial.gestionnaire_contractuel`,
`ContratCommercial.cree_par`, `DemandeAvenant.demandeur`,
`DemandeAvenant.validateur`, `MouvementPerimetre.auteur` → tous
`ForeignKey(Utilisateur, on_delete=SET_NULL)` (vérifié : `Utilisateur`
dans `registre/models.py`, hérite de `AbstractUser`, pas de champ
`is_active` redéfini — le champ Django standard suffit pour le signal
d'absence de gestionnaire actif, aucune contradiction avec l'architecture).
`MouvementPerimetre.etablissement`/`batiment`,
`LigneDemandeAvenant.etablissement`/`batiment` → `ForeignKey(...,
on_delete=PROTECT)` vers les modèles existants `Etablissement`/`Batiment`
(vérifiés, lignes 109 et 156 de `models.py`), sans aucune modification
de ces deux modèles.

**Champs et contraintes** : voir §1.1/§1.2/§1.3 de l'architecture
technique. **Index** : aucun index explicite nouveau jugé nécessaire au-delà
de ceux que Django crée automatiquement sur les clés étrangères — le volume
attendu (un contrat actif, quelques dizaines de mouvements par an) ne
justifie pas d'index composé dédié ; à revoir seulement si l'usage réel
montre un besoin, cohérent avec `POLITIQUE-001`.

## 2. Historisation

- **Renouvellement** : nouvelle ligne `ContratCommercial`, jamais de
  modification d'une ligne existante ; `contrat_precedent` (FK self)
  relie explicitement les deux.
- **Gestionnaire contractuel** : porté par `ContratCommercial`, pas par
  `Utilisateur` — chaque ligne historique garde sa propre référence.
- **Dates début/fin** : `date_fin` toujours calculée
  (`date_debut + duree_engagement_mois`), jamais saisie indépendamment.
- **Statut** : stocké, mais jamais seule source de vérité — une
  incohérence avec les dates est signalée, jamais corrigée en silence
  (§3.1 de l'architecture technique).
- **Reconstruction du périmètre historique** : fonction pure
  `perimetre_a_date(contrat, date)`, rejoue les `MouvementPerimetre`
  jusqu'à la date donnée — ne dépend ni de l'état actuel des objets
  (`Etablissement.actif`), ni de leur existence continue en base
  (`on_delete=PROTECT` + champs `*_historique` en snapshot texte,
  §1.2 de l'architecture technique).

**Fichier concerné** : nouveau `registre/contractualisation.py` (voir §4).

## 3. Périmètre contractuel

- **Établissements et bâtiments** : suivis exclusivement via
  `MouvementPerimetre`, jamais via `Etablissement.actif`/`Batiment.actif`.
- **Mouvements explicites** : un `MouvementPerimetre` par objet — un
  établissement ajouté avec ses bâtiments produit plusieurs lignes, pas
  une seule ligne agrégée (tranché le 21/09/2026, structure déjà imposée
  par `LigneDemandeAvenant`).
- **Distinction stricte avec `actif`, vérifiée dans le code actuel** :
  `Etablissement.actif` (ligne 139 de `models.py`, « Site actif ») et
  `Batiment.actif` (ligne 182, « Bâtiment actif (registre facturable) »)
  restent des champs purement opérationnels. Confirmé : rien dans
  `registre/views.py` ne les relie aujourd'hui à une notion de
  facturation réelle — seul le `verbose_name` de `Batiment.actif`
  emploie le mot « facturable », sans mécanisme derrière. Le
  développement P5-L1 ne touche **jamais** ces deux champs, dans aucun
  sens (ni lecture pour la facturation, ni écriture depuis le module
  commercial).

## 4. Workflow `DemandeAvenant`

**Fichier concerné (nouveau)** : `registre/contractualisation.py` —
même principe que `registre/tableau_bord.py` (vérifié : module de
logique métier pure, sans dépendance à `request`/`response`, déjà
adopté au lot P4-L1 pour la même raison) et `registre/permissions.py`.

Trois fonctions de service, chacune dans une transaction :
- `soumettre_demande(demandeur, contrat_commercial, lignes)` → crée la
  `DemandeAvenant` (`EN_ATTENTE`) et ses `LigneDemandeAvenant`.
- `valider_demande(demande, validateur, commentaire='')` → vérifie les
  droits (§6), crée un `MouvementPerimetre` par ligne (même
  `date_effet`), passe `VALIDEE`.
- `rejeter_demande(demande, validateur, commentaire)` → passe
  `REJETEE`, ne touche jamais `MouvementPerimetre`.

**Un habilité peut valider sa propre demande** : même fonction
`valider_demande`, aucun chemin de code séparé — la vérification porte
sur les droits du `validateur` passé en paramètre, pas sur une
comparaison avec le `demandeur` (donc demandeur == validateur est un
cas normal, pas un cas particulier à coder).

**`MouvementPerimetre` créé uniquement à la validation** : ces trois
fonctions sont le seul point d'écriture. Aucune vue n'appelle
`MouvementPerimetre.objects.create(...)` directement — à faire
respecter en revue de code, pas par une contrainte technique
supplémentaire (cohérent avec le reste du projet, qui s'appuie sur la
discipline de revue plutôt que sur des verrous applicatifs superflus).

## 5. Calcul commercial

**Fichier concerné** : `registre/contractualisation.py`.

- `tarif_mensuel(contrat, date=None)` — §3.2 de l'architecture technique.
- `montant_maintenance_annuelle(contrat, date_anniversaire)` — §3.3.
- `date_anniversaire_maintenance(contrat, annee=None)` — dérivée de
  `date_debut` (tranché le 21/09/2026).
- `premier_du_mois_suivant(date=None)` — date d'effet par défaut,
  jamais modifiable vers le passé ou le mois courant (validé en
  `clean()`).
- Tarifs `24/36/48` mois et maintenance : **valeurs figées sur
  `ContratCommercial` à la signature** (§1.1), jamais recalculées
  après coup si le barème change — aucune table de barème séparée
  nécessaire pour ce lot (le barème n'existe nulle part dans le code
  aujourd'hui ; il est appliqué manuellement par
  admin/responsable_securite au moment de créer/renouveler le contrat,
  cohérent avec le fait que PSM2S n'a pas encore de client en
  production réelle facturé).
- **Aucun prorata, effet au 1er du mois suivant** : porté par
  `date_effet`/`date_effet_souhaitee`, pas par une logique de calcul
  séparée.

## 6. Permissions

**Fichiers concernés, vérifiés** : `registre/permissions.py` (décorateurs
`acces_requis`, `gestionnaire_requis`, `referentiel_partenaires_requis`,
`verifier_acces_etablissement`, `get_etablissement_ou_404`) et
`registre/views.py` (usage de ces décorateurs).

- **Réutilisation stricte du mécanisme existant** : `acces_requis(*roles)`
  (ligne 17) est le décorateur générique dont dérivent tous les autres.
  `referentiel_partenaires_requis` (ligne 47, « admin + responsable
  sécurité seuls, pas Directeur ») est **l'exact précédent** du futur
  `commercial_gestion_requis` — même patron, à réutiliser tel quel,
  aucun nouveau mécanisme à inventer.
- **Droit opérationnel vs droit contractuel** : `nouveau_etablissement`
  reste `gestionnaire_requis` (admin/responsable_securite/directeur,
  inchangé) ; soumettre une `DemandeAvenant` suit le même décorateur.
  Valider/rejeter/consulter-intégralement/gérer le contrat : nouveau
  décorateur `commercial_gestion_requis` = `acces_requis('admin',
  'responsable_securite')`, littéralement copié sur
  `referentiel_partenaires_requis`.
- **`gestionnaire_contractuel` vérifié au niveau du contrat**, pas du
  rôle : fonction dédiée `verifier_acces_gestion_contrat(user,
  contrat)`, autorise si `user.role in ('admin', 'responsable_securite')
  or user.is_superuser or contrat.gestionnaire_contractuel_id == user.id`.
- **Gestionnaire désactivé** : `contrat.gestionnaire_contractuel.is_active`
  vérifié dans le signal (§3.4 de l'architecture technique), jamais dans
  la fonction de permission elle-même — un gestionnaire désactivé perd
  simplement sa capacité à se connecter (comportement Django standard,
  déjà comment `is_active=False` fonctionne partout ailleurs), donc il
  ne peut plus valider de fait ; **aucune logique spécifique à coder
  pour ça** au-delà du signal d'alerte. Le contrat reste `ACTIF`, jamais
  invalidé.

### Contradiction relevée avec la documentation P5-L1

Les deux documents d'architecture emploient la formule « jamais de 403
brut, toujours 404 » comme règle générale de PSM2S. **Vérification du
code actuel : c'est inexact à ce niveau de généralité.** Deux mécanismes
coexistent, avec des comportements différents :
- `acces_requis`/`gestionnaire_requis`/`referentiel_partenaires_requis`
  (permissions.py, ligne 17) : en cas de refus, **redirection vers
  `registre:dashboard`** — jamais un 404, jamais un 403.
- `verifier_acces_etablissement`/`get_etablissement_ou_404`
  (permissions.py, ligne 139) : en cas de refus, **Http404**, précisément
  pour ne pas révéler l'existence d'un objet rattaché à un établissement
  hors périmètre.

La règle « 404 systématique » ne s'applique donc qu'au deuxième
mécanisme (accès à un objet précis hors périmètre), pas au premier
(rôle insuffisant pour une action). **Conséquence pour P5-L1** :
`commercial_gestion_requis` (décorateur de rôle) doit suivre le premier
patron — **redirection**, pas 404. Reste une question ouverte (§«
décisions restantes ») : `verifier_acces_gestion_contrat`, qui porte sur
une donnée (le `gestionnaire_contractuel` désigné) et non sur un rôle
statique, doit-il suivre le patron 404 (comme `verifier_acces_etablissement`,
auquel il ressemble le plus par sa forme) ou le patron redirection (comme
les décorateurs de rôle, puisqu'il n'y a rien à cacher — l'existence du
contrat n'est un secret pour personne) ? Les deux se défendent ; ce n'est
pas tranché dans la documentation existante.

## 7. Interface

**Fichiers concernés, vérifiés** :
`Templates/registre/dashboard.html` (page unique listant les
établissements, avec un bloc conditionnel `{% if directeur_indicateurs %}`
en haut — **pas de page séparée par rôle** : toute nouvelle section pour
admin/responsable_securite/gestionnaire s'ajoute au même template, en
bloc conditionnel analogue, pas en nouvelle page) ;
`Templates/registre/nouveau_etablissement.html` (déjà modifié une fois
pour le chantier tablette, cf. Phase 4) ; pas de dossier
`Templates/registre/contrat*` existant — tout est à créer.

**Nouveaux templates** : `contrat_detail.html`, `contrat_historique.html`,
`demande_avenant_form.html` (écran d'impact chiffré, texte déjà rédigé
par Phil), `demande_avenant_liste.html`, `demande_avenant_validation.html`,
`renouvellement_form.html`, `resiliation_form.html`.

**Intégration minimale à l'existant** :
- `detail_etablissement.html` (affiché juste après création, via la
  redirection déjà en place) : bandeau informatif si l'établissement est
  hors périmètre contractuel, avec lien vers la soumission d'une demande
  si l'utilisateur y est autorisé.
- `dashboard.html` : nouveau bloc conditionnel (compteur de demandes en
  attente), visible seulement admin/responsable_securite/gestionnaire —
  ajouté à côté du bloc `directeur_indicateurs` existant, sans le
  modifier.

**Écrans couverts** : consultation du contrat (§4.1/§4.2 de
l'architecture technique — niveau intégral ou scopé selon le rôle),
ajout/retrait d'établissement ou bâtiment (formulaire `DemandeAvenant`),
écran d'impact financier + avertissement avenant (soumission et
validation), validation/rejet, renouvellement, résiliation.

## 8. Tests

**Fichier concerné** : `registre/tests.py` (vérifié : fichier unique,
195 tests actuels, aucun fichier de tests séparé dans le projet à ce
jour — pas de précédent pour un découpage en plusieurs fichiers ; à
signaler comme point de vigilance si le volume ajouté par P5-L1 rend le
fichier difficile à lire, mais pas une décision à anticiper ici).

Classes de tests prévues, par analogie avec `BaseAccesEtablissement`
déjà en place (lignes 28-60) :
- **Modèles** : contrainte un seul `ContratCommercial` `ACTIF`, calcul
  de `date_fin`, cohérence `statut`/dates.
- **Calculs** : `perimetre_a_date` sur un historique multi-mouvements
  (reprenant l'exemple de Phil : 01/01 puis 01/04), tarif mensuel
  évolutif, reconstruction indépendante de l'état actuel des objets.
- **Dates d'effet** : toujours 1er du mois, jamais rétroactives.
- **Permissions par rôle** : matrice complète (admin, responsable_securite,
  gestionnaire_contractuel, directeur non gestionnaire limité à son
  périmètre, autres rôles refusés) — **en tenant compte de la
  contradiction relevée au §6** : tests de redirection pour les
  décorateurs de rôle, tests de 404 uniquement pour les vérifications
  objet, pas l'inverse.
- **Gestionnaire contractuel** : désignation, changement au
  renouvellement (pré-rempli, validation explicite obligatoire),
  désactivation du compte → signal sans invalidation du contrat.
- **Demandes d'avenant** : soumission, validation (produit les bons
  `MouvementPerimetre`), rejet (n'en produit aucun, jamais lu par
  `perimetre_a_date`), demandeur-validateur unique.
- **Historique** : `contrat_precedent`, ancien contrat inchangé après
  renouvellement.
- **Renouvellement/résiliation** : voir §2.
- **Non-régression** : suite complète (195 tests actuels + nouveaux)
  systématiquement rejouée, `makemigrations --check --dry-run` et
  `manage.py check` avant chaque commit — même discipline que le
  correctif du 21/09/2026.

**Point de vigilance vérifié** : `EtablissementForm` inclut `actif`
comme case à cocher (`forms.CheckboxInput`) — une case absente du POST
est interprétée comme décochée (rencontré concrètement lors du
correctif du 21/09/2026). Tout test simulant un POST vers un formulaire
avec une case à cocher liée à un booléen par défaut `True` devra
explicitement l'inclure, sous peine de faux échec.

## 9. Migration et déploiement

- **Migration** : une seule, `registre/migrations/0024_contractualisation.py`
  (vérifié : `0023_correspondantlocal.py` est la dernière migration
  existante, aucune migration `0024` présente). Aucune donnée existante
  à transformer — les quatre modèles sont entièrement nouveaux, pas de
  migration de données comme celle nécessaire à P4-L3.
- **Données initiales** : aucune fixture nécessaire. Le premier
  `ContratCommercial` (statut initial, tarifs, gestionnaire) sera créé
  manuellement par admin/responsable_securite via l'écran prévu, pas par
  une migration de données — cohérent avec le fait que PSM2S n'a pas
  encore de contrat commercial réel à modéliser rétroactivement.
- **Ordre de déploiement** : migration d'abord (`migrate`), puis code
  (vues/templates) — ordre standard déjà suivi pour tous les lots
  précédents (`PROC-001`/`PROC-002`), pas de spécificité nouvelle ici.

## 10. Découpage en lots

Découpage proposé, chaque lot testé et validé avant le suivant :

**Lot A — Modèles et migration** (dépend de : rien)
Les 4 modèles, la migration, les contraintes `clean()`. Tests : §8
« Modèles », « Calculs » (les fonctions de `contractualisation.py`
peuvent être écrites et testées sans aucune vue). Rien de visible dans
l'application à ce stade.

**Lot B — Permissions** (dépend de : Lot A)
`commercial_gestion_requis`, `verifier_acces_gestion_contrat`,
tranchage de la contradiction du §6. Tests : §8 « Permissions par rôle ».
Toujours rien de visible (pas de vue encore).

**Lot C — Contrat commercial** (dépend de : Lot B)
Vues/formulaires de consultation, création initiale, renouvellement,
résiliation. Templates `contrat_detail.html`, `contrat_historique.html`,
`renouvellement_form.html`, `resiliation_form.html`. Tests : §8
« Gestionnaire contractuel », « Historique », « Renouvellement/résiliation ».
Premier lot visible et utilisable par Phil pour tester en conditions
réelles.

**Lot D — Workflow `DemandeAvenant`** (dépend de : Lot C)
Soumission, validation, rejet, écran d'impact chiffré. Intégration à
`nouveau_etablissement`/`detail_etablissement` (bandeau informatif).
Tests : §8 « Demandes d'avenant ». Lot le plus visible pour Phil (répond
directement au scénario du directeur qui reçoit un établissement).

**Lot E — Tableau de bord et finitions** (dépend de : Lot D)
Compteur « demandes en attente » sur `dashboard.html`, amélioration
nominative du signal de dépassement de périmètre (§4.4 de l'architecture
technique). Non bloquant pour l'usage réel — peut être reporté sans
casser les lots précédents.

---

## Points nécessitant encore une décision métier

1. **§6** : `verifier_acces_gestion_contrat` (refus d'un directeur non
   gestionnaire sur une action de gestion) doit-il suivre le patron
   redirection (comme les décorateurs de rôle existants) ou le patron
   404 (comme les vérifications d'objet type `verifier_acces_etablissement`) ?
   Recommandation : redirection, pour rester cohérent avec le mécanisme
   dont il se rapproche le plus fonctionnellement (un rôle insuffisant,
   pas un objet à cacher) — mais c'est un choix, pas une évidence.
2. **§8** : le fichier `registre/tests.py` unique va grossir
   significativement avec P5-L1 (estimation : 30 à 50 tests). Faut-il
   l'accepter tel quel (cohérent avec la convention actuelle) ou ouvrir,
   séparément de P5-L1, un lot de réorganisation des tests en plusieurs
   fichiers ? Pas nécessaire pour développer P5-L1, mais à anticiper.
3. Aucun autre point bloquant identifié — le reste du plan découle
   directement de l'architecture déjà validée et du code actuel vérifié.

---

*Ce plan est soumis à validation DT. Aucun développement ne commence
avant relecture et feu vert explicite de Phil, lot par lot (§10).*
