# Analyse technique — Anomalie C4 : IDOR

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Objet : proposition technique de correction de l'anomalie C4 (Insecure Direct Object Reference), pour validation architecturale **avant** tout développement.

> **Aucune modification n'a été apportée au code.** Ce document est exclusivement un rapport d'analyse. Aucun patch, commit, migration ni renommage n'a été produit.

---

## 0. Rappel de l'anomalie

C4 = **IDOR** : un utilisateur authentifié accède à des objets qui ne relèvent pas de son périmètre en manipulant l'identifiant présent dans l'URL (ex. `/etablissement/42/`, `/document/17/supprimer/`). Les **listes** de PSM2S sont filtrées par rôle, mais les vues de **détail, édition et suppression** récupèrent l'objet par sa clé primaire sans vérifier qu'il appartient à un établissement autorisé pour l'utilisateur.

---

## 1. Localisation de la vulnérabilité

### 1.1 Fichiers concernés

- `registre/views.py` — siège principal de la vulnérabilité (la quasi-totalité des vues à paramètre `pk`/`etab_pk`).
- `registre/forms.py` — vulnérabilité secondaire : certains `queryset` de champs de sélection ne sont pas filtrés par périmètre (`InterventionForm`, et les formulaires où `etab_pk` n'est pas transmis).
- `registre/permissions.py` — les décorateurs contrôlent le **rôle**, jamais l'**appartenance de l'objet** ; ce n'est pas un défaut du fichier mais la limite structurelle à combler.
- `registre/models.py` — porte les relations qui définissent le périmètre (source de la règle d'autorisation), et l'incohérence `peut_tout_voir` (voir §3.4).
- `config/urls.py` / `registre/urls.py` — exposent les routes paramétrées (aucune correction attendue ici, mais elles matérialisent la surface d'attaque).

### 1.2 Mécanisme de référence existant

Le helper `_get_etab_ids_autorises(user)` (`views.py` ~l.23) renvoie déjà l'ensemble des établissements autorisés (`None` = accès total pour admin/responsable/superuser). Il est **correctement utilisé dans les listes** (`controles_global`, `tickets_global`, `interventions`) mais **absent des vues objet**. C'est la brique de correction, déjà disponible.

### 1.3 Vues concernées (cartographie)

**A. Accès direct par établissement (`etab_pk`) — sans vérification de périmètre**
`nouveau_controle`, `modifier_etablissement`, `nouveau_batiment`, `nouveau_document`, `carnet_eau`, `nouveau_reseau_eau`, `nouvelle_analyse_eau`, `nouvelle_visite_commission`, `nouveau_contrat`, `duerp_nouveau`, `accessibilite_detail`, `accessibilite_grille`, `accessibilite_formation_ajouter`, `accessibilite_piece_ajouter`, `accessibilite_action_ajouter`, `accessibilite_imprimer`, `accessibilite_signer`.

**B. Accès direct par objet enfant (`pk` d'un contrôle, document, ticket, etc.) — sans remontée vers l'établissement autorisé**
`detail_etablissement` (vérifie **uniquement** le rôle prestataire), `modifier_controle`, `registre_pdf`, `historique_controle`, `nouvelle_realisation`, `modifier_batiment`, `supprimer_batiment`, `modifier_document`, `supprimer_document`, `modifier_ticket`, `supprimer_ticket`, `ajouter_piece_jointe`, `supprimer_piece_jointe`, `modifier_intervention`, `modifier_analyse_eau`, `supprimer_analyse_eau`, `nouveau_point_prelevement`, `detail_visite_commission`, `modifier_visite_commission`, `supprimer_visite_commission`, `nouvelle_prescription`, `modifier_prescription`, `nouvelle_action_prescription`, `supprimer_action_prescription`, `modifier_contrat`, `supprimer_contrat`, `duerp_detail`, `duerp_checklist`, `duerp_plan_action`, `duerp_action_creer`, `duerp_action_modifier`, `duerp_creer_ticket`, `duerp_modifier`, `duerp_imprimer`, `duerp_signer`, `duerp_supprimer_signature`, `accessibilite_creer_ticket`.

**C. Périmètre « équipe » partiellement traité**
`liste_utilisateurs`, `modifier_utilisateur`, `nouvel_utilisateur` (scopés directeur), mais `modifier_niveau_factotum` ne revérifie pas que le factotum ciblé relève d'un site du directeur.

**Vues non concernées (déjà sûres)** : `dashboard`, `controles_global`, `tickets_global`, `interventions` (filtrées par `_get_etab_ids_autorises`) ; `mon_profil` (agit sur `request.user`) ; vues admin-only (`archiver_etablissement`, périodicités, groupes) où la restriction de rôle suffit au besoin métier.

### 1.4 Modèles concernés

Tous les modèles rattachés directement ou indirectement à `Etablissement` : `ControleEtablissement`, `Batiment`, `Document`, `RealisationControle`, `TicketTravaux`, `PieceJointeTicket`, `Intervention`, `Contrat`, `VisiteCommission`, `Prescription`, `ActionPrescription`, `ReseauEau`, `PointPrelevement`, `AnalyseEau`, `DUERP` (+ `UniteTravail`, `EvaluationRisque`, `PlanActionDUERP`), `RegistreAccessibilite` (+ `EvaluationZone`, `FormationPersonnel`, `PieceAdministrative`, `ActionMiseConformite`). Le périmètre d'un utilisateur est défini par `EtablissementUtilisateur` (+ dérivés tickets/interventions pour factotum/prestataire).

### 1.5 URL concernées

Toutes les routes paramétrées de `registre/urls.py` correspondant aux vues des catégories A, B et C ci-dessus (routes en `<int:pk>`, `<int:etab_pk>`, `<int:controle_pk>`, `<int:ticket_pk>`, `<int:visite_pk>`, `<int:prescription_pk>`, `<int:duerp_pk>`, `<int:unite_pk>`, `<int:action_pk>`, `<int:reseau_pk>`).

---

## 2. Analyse technique

### 2.1 Pourquoi la vulnérabilité existe

L'autorisation dans PSM2S est faite à **deux niveaux seulement** : (1) authentification (`@login_required`), (2) rôle (`@gestionnaire_requis`, `@factotum_niveau_requis`, etc.). Il manque le **troisième niveau, l'autorisation au niveau de l'instance** : « cet utilisateur a-t-il le droit d'agir sur *cet objet précis* ? ».

Les vues objet suivent le motif :
```
obj = get_object_or_404(Modele, pk=pk)   # ← aucune contrainte de périmètre
```
`get_object_or_404` ne connaît que la clé primaire. Le périmètre existe pourtant en base (`EtablissementUtilisateur`) et un helper le calcule déjà (`_get_etab_ids_autorises`), mais il n'est pas convoqué dans ces vues. La vulnérabilité est donc une **omission systématique**, pas une erreur de conception des données.

### 2.2 Comment elle pourrait être exploitée

L'attaquant est un utilisateur **légitimement authentifié** mais à périmètre restreint (directeur d'un site, factotum, prestataire). Il modifie l'identifiant numérique dans l'URL. Les identifiants étant séquentiels (`BigAutoField`), l'énumération est triviale (1, 2, 3…).

### 2.3 Données exposées — exemples concrets PSM2S

- **Lecture inter-établissements** : un directeur du site A ouvre `/etablissement/<id_du_site_B>/` → `detail_etablissement` ne vérifie que le rôle prestataire ; il consulte l'intégralité du registre du site B (contrôles, documents, tickets, contrats, DUERP, commissions). De même `/duerp/<pk>/` expose l'évaluation des risques professionnels d'un autre établissement (`peut_tout_voir` aggrave le cas pour le directeur, cf. E5 de l'audit).
- **Téléchargement de pièces sensibles** : `/etablissement/<id_B>/registre/` (`registre_pdf`) ou `/commission/<pk>/` (`detail_visite_commission`) donnent accès aux PV de commission de sécurité et prescriptions d'un site non autorisé.
- **Modification/suppression** : un factotum de niveau 2 appelle `/tickets/<pk>/modifier/`, `/document/<pk>/supprimer/`, `/eau/analyse/<pk>/supprimer/` ou `/controles/<pk>/modifier/` sur des objets d'un autre établissement → altération ou destruction de données réglementaires d'un site tiers, y compris suppression du fichier physique associé.
- **Escalade organisationnelle** : `/administration/utilisateurs/<pk>/niveau/` (`modifier_niveau_factotum`) — un directeur peut élever le niveau d'habilitation d'un factotum rattaché à un autre site.
- **Fuite via menus déroulants** : `InterventionForm` liste **tous** les tickets non clôturés (titres inclus) quel que soit le périmètre de l'utilisateur.

Gravité : **Critique** — la confidentialité, l'intégrité et la traçabilité de données réglementaires opposables (sécurité incendie, RGPD, signatures) sont en jeu.

---

## 3. Architecture actuelle

### 3.1 Gestion des utilisateurs

Modèle `Utilisateur` (hérite d'`AbstractUser`, `AUTH_USER_MODEL` dès l'origine) avec un champ `role` (admin, responsable_securite, directeur, factotum, prestataire) et `niveau_factotum` (1-4). Propriétés d'aide : `est_admin`, `est_responsable`, `peut_tout_voir`, `peut_voir_etablissement(etab)`.

### 3.2 Relations utilisateur ↔ établissement ↔ objets métier

- Rattachement principal : `EtablissementUtilisateur` (M2M explicite utilisateur ↔ établissement, avec `principal`).
- Rattachements dérivés : factotum et prestataire gagnent l'accès aux établissements via `TicketTravaux.responsable` et `Intervention.saisie_par`.
- Tous les objets métier pointent vers `Etablissement` directement (FK `etablissement`) ou indirectement (`controle → etablissement`, `visite → etablissement`, `point → reseau → etablissement`, `unite → duerp → etablissement`, `evaluation_zone → registre → etablissement`, etc.). **Le chemin de remontée vers l'établissement existe pour chaque objet** — c'est ce qui rend la correction déterministe.

### 3.3 Mécanismes de contrôle d'accès existants

1. `@login_required` (authentification).
2. Décorateurs de rôle dans `permissions.py` (`acces_requis`, `admin_requis`, `gestionnaire_requis`, `operateur_requis`, `factotum_niveau_requis`).
3. `_get_etab_ids_autorises(user)` — calcule le périmètre ; **utilisé dans les listes uniquement**.
4. Vérifications ad hoc éparses : `detail_etablissement` (prestataire), `duerp_liste` (`peut_tout_voir`), scoping directeur dans les vues utilisateurs, `DroitSignature.peut_signer` pour les signatures.

### 3.4 Points faibles de cette architecture

- **Autorisation d'instance absente** : le niveau 3 (objet) n'existe pas de façon systématique.
- **Trois systèmes de droits parallèles et divergents** : décorateurs, propriétés de modèle (`peut_tout_voir`), et `_get_etab_ids_autorises` — qui se contredisent (le directeur est « tout-voir » côté propriété mais « restreint » côté helper).
- **Vérifications dispersées et non réutilisables** : chaque contrôle ad hoc est une occasion d'oubli (et il y a déjà des oublis).
- **Identifiants séquentiels** : facilitent l'énumération (aggravant, non causal).
- **Formulaires non filtrés** : angle mort supplémentaire côté sélections.

---

## 4. Propositions de correction

Toutes compatibles Django et avec l'architecture PSM2S. Aucune ne requiert de migration de schéma.

### Option 1 — Helper d'autorisation d'objet centralisé (garde-fou explicite dans chaque vue)

**Principe** : créer une fonction utilitaire unique, p. ex. `get_objet_ou_403(model, pk, user, chemin_etablissement)`, qui récupère l'objet puis vérifie que son établissement (atteint via le chemin de FK fourni) appartient à `_get_etab_ids_autorises(user)` ; sinon `Http404`/`PermissionDenied`. Chaque vue objet remplace son `get_object_or_404` par cet appel. `_get_etab_ids_autorises` devient la **source unique de vérité**.

- **Avantages** : explicite et lisible ; réutilise l'existant ; correction incrémentale vue par vue (idéal pour un protocole anti-régression) ; aucun schéma modifié ; testable unitairement.
- **Inconvénients** : nécessite d'éditer chaque vue concernée (~40) ; discipline requise pour les futures vues (un oubli reste possible).
- **Impact sur le code existant** : moyen en surface (beaucoup de vues), faible en profondeur (1 ligne modifiée par vue + 1 helper).
- **Impact performances** : négligeable (`_get_etab_ids_autorises` déjà appelé dans les listes ; 1 requête ensembliste par vue, cacheable par requête).
- **Risque de régression** : faible et **maîtrisable** car chaque vue est traitée et testée isolément.

### Option 2 — QuerySets et Managers filtrés par périmètre (`Model.objects.pour_utilisateur(user)`)

**Principe** : ajouter à chaque modèle métier un `Manager`/`QuerySet` exposant `.pour_utilisateur(user)` qui applique le filtre d'établissement. Les vues récupèrent l'objet via ce queryset (`get_object_or_404(Modele.objects.pour_utilisateur(request.user), pk=pk)`).

- **Avantages** : logique de périmètre au plus près des données ; réutilisable en liste **et** en détail ; réduit la duplication ; élégant et « très Django ».
- **Inconvénients** : plus de fichiers touchés (modèles + vues) ; définir le chemin de remontée pour chaque modèle ; courbe d'apprentissage ; changement plus large donc revue plus lourde.
- **Impact code existant** : moyen à élevé (models.py + views.py).
- **Impact performances** : équivalent à l'option 1, voire meilleur (filtre poussé en SQL).
- **Risque de régression** : moyen — modifier les managers peut affecter des requêtes existantes s'il n'est pas parfaitement ciblé.

### Option 3 — Mixin/décorateur d'autorisation d'objet

**Principe** : décorateur paramétrable (`@objet_autorise(Modele, chemin='etablissement')`) qui injecte l'objet vérifié dans la vue, ou mixin si migration vers des CBV.

- **Avantages** : très peu de code dans le corps des vues ; motif réutilisable.
- **Inconvénients** : PSM2S est **100 % en vues fonctions** — un mixin imposerait une réécriture en CBV (hors périmètre, risqué) ; un décorateur paramétrable qui gère la diversité des chemins de FK et des noms de paramètres (`pk`, `etab_pk`, `controle_pk`…) devient complexe et moins lisible.
- **Impact code existant** : moyen ; incohérent avec le style FBV actuel si CBV.
- **Impact performances** : négligeable.
- **Risque de régression** : moyen (magie du décorateur, cas particuliers nombreux).

### Option 4 — Framework de permissions objet (django-guardian, permissions par ligne)

**Principe** : permissions par objet stockées en base via une librairie dédiée.

- **Avantages** : très granulaire, standard de l'écosystème.
- **Inconvénients** : **surdimensionné** ici — le périmètre est déjà entièrement déductible des FK existantes ; ajoute une dépendance, des tables, une migration et une synchronisation permanente ; contraire au principe de simplicité de PSM2S.
- **Impact / risque** : élevé. **Écarté.**

---

## 5. Solution recommandée

**Option 1 — helper d'autorisation d'objet centralisé**, avec adoption de `_get_etab_ids_autorises` comme **source unique de vérité** (et neutralisation progressive de `peut_tout_voir` pour supprimer l'incohérence E5).

**Justification**
- **Compatibilité maximale** avec l'existant : conserve le style FBV, réutilise le helper déjà présent et déjà éprouvé en liste — donc cohérence immédiate entre listes et détails.
- **Correction incrémentale** : chaque vue est corrigée et testée indépendamment, ce qui colle exactement au protocole PSM2S « une chose à la fois, zéro régression ». C'est le critère décisif face à l'option 2, plus globale et à revue plus lourde.
- **Zéro migration, zéro changement de schéma** : conforme aux contraintes de la mission.
- **Lisibilité** : le garde-fou est visible dans chaque vue, ce qui facilite l'audit futur, alors que le décorateur (option 3) masque la logique et cadre mal avec la diversité des chemins de FK.

L'option 2 est un **excellent second choix** et pourra être adoptée ultérieurement en complément (managers filtrés) une fois la surface stabilisée ; mais commencer par l'option 1 minimise le risque immédiat. L'option 3 est écartée (incompatibilité de style / complexité), l'option 4 également (surdimensionnée).

Recommandation complémentaire : traiter en parallèle l'angle mort **formulaires** (filtrer les `queryset` de sélection par périmètre) et prévoir à terme des identifiants non séquentiels (UUID/slug) en défense en profondeur — hors périmètre C4 immédiat.

---

## 6. Impact sur le projet

### 6.1 Fichiers à modifier (lors de l'implémentation future, non réalisée)
- `registre/views.py` : ajout du helper + substitution du `get_object_or_404` dans les vues des catégories A, B, C (§1.3).
- `registre/forms.py` : filtrage des `queryset` de `InterventionForm` (et vérification des formulaires recevant `etab_pk`).
- `registre/models.py` : alignement de `peut_tout_voir`/`peut_voir_etablissement` sur `_get_etab_ids_autorises` (cohérence E5) — **sans migration**.
- `registre/tests.py` : création de la suite de tests d'accès (aujourd'hui vide).
- `registre/permissions.py` : éventuel point d'accueil du helper si l'on souhaite le regrouper avec les décorateurs (choix d'emplacement à trancher par le DT).

### 6.2 Vues concernées
Les ~40 vues listées au §1.3 (catégories A et B), plus `modifier_niveau_factotum` (catégorie C). Vues déjà sûres à **ne pas** toucher : listes filtrées, `mon_profil`, vues admin-only.

### 6.3 Modèles concernés
Aucun changement structurel. Seuls les **chemins de remontée** vers `Etablissement` sont utilisés (déjà tous existants). Ajustement comportemental sur les propriétés de droit du modèle `Utilisateur`.

### 6.4 Tests à prévoir
- Tests unitaires du helper (périmètre autorisé / refusé / accès total admin).
- Tests d'accès par rôle et par vue : pour chaque vue sensible, un utilisateur hors périmètre doit recevoir 403/404 en **lecture, édition et suppression**.
- Tests de non-régression : un utilisateur **dans** son périmètre conserve tous ses accès.
- Tests des formulaires : les `queryset` de sélection ne contiennent que des objets autorisés.
- Cas limites : superuser, responsable/admin (accès total), factotum via ticket assigné, prestataire via ticket assigné.

### 6.5 Points de vigilance
- **Choix 403 vs 404** : renvoyer 404 (plutôt que 403) évite de révéler l'existence de l'objet — à trancher par le DT (recommandation : 404).
- **Ne pas casser les accès dérivés** factotum/prestataire (tickets/interventions) : le helper doit refléter exactement la logique de `_get_etab_ids_autorises`.
- **Cohérence avec `detail_etablissement`** qui a déjà une demi-vérification (prestataire) : la remplacer, pas l'empiler.
- **Suppressions de fichiers physiques** (documents, PV, signatures) : la vérification doit précéder toute suppression sur disque.
- **Régression Lot 1 (Calendrier)** : la vue `calendrier` filtre déjà correctement ; s'assurer que les liens qu'elle génère vers `modifier_controle` restent cohérents avec les nouveaux garde-fous (un factotum voit des événements mais sera refusé à l'édition — comportement attendu, à documenter).
- **`peut_tout_voir`** : sa neutralisation touche `duerp_liste` — à tester spécifiquement.

---

## 7. Plan d'implémentation (par étapes indépendantes)

Chaque étape est autonome, livrable et testable seule, conformément au protocole PSM2S.

- **Étape 0 — Préparation** : geler la liste exhaustive des vues (annexe §1.3), écrire d'abord les **tests d'accès qui échouent** (rouge) pour matérialiser la vulnérabilité et servir de filet.
- **Étape 1 — Socle** : introduire le helper d'autorisation d'objet + tests unitaires. Aucune vue modifiée → aucun impact fonctionnel. Faire de `_get_etab_ids_autorises` la référence unique.
- **Étape 2 — Établissement** : sécuriser `detail_etablissement`, `modifier_etablissement`, `registre_pdf` (cœur de la fuite de lecture). Tests + validation.
- **Étape 3 — Contrôles & réalisations** : `modifier_controle`, `nouveau_controle`, `nouvelle_realisation`, `historique_controle`, bâtiments.
- **Étape 4 — Documents & tickets & interventions** : documents, pièces jointes, tickets, `modifier_intervention` + filtrage `InterventionForm`.
- **Étape 5 — Commissions & contrats & eau** : visites/prescriptions/actions, contrats, carnet eau.
- **Étape 6 — DUERP & accessibilité** : toutes les vues des deux modules + neutralisation de `peut_tout_voir` (impacte `duerp_liste`).
- **Étape 7 — Administration d'équipe** : `modifier_niveau_factotum` et revérification du scoping directeur.
- **Étape 8 — Clôture** : revue transversale (grep des `get_object_or_404` restants), campagne de tests complète, documentation, validation DT.

Chaque étape se termine par : tests verts, contrôle de non-régression sur le périmètre autorisé, validation avant l'étape suivante.

---

## 8. Estimation

| Critère | Évaluation |
|---|---|
| **Complexité technique** | Moyenne — mécanique simple mais transversale (~40 vues, cas dérivés factotum/prestataire à respecter). |
| **Niveau de risque** | Moyen si traité par étapes (recommandé) ; élevé si tout en une passe. Le risque principal est de **sur-restreindre** un accès légitime → couvert par les tests de non-régression. |
| **Temps de développement** | Étape 1 : ~0,5 j. Étapes 2 à 7 : ~0,5 à 1 j chacune selon le module → ~4 à 6 j. Formulaires + `peut_tout_voir` : ~0,5 j. **Total dev ≈ 5 à 7 jours.** |
| **Temps de tests** | Rédaction de la suite d'accès (toutes vues × rôles) + non-régression : **≈ 3 à 4 jours**, dont une part réalisée en amont (Étape 0, approche « tests d'abord »). |
| **Total indicatif** | **≈ 8 à 11 jours** développement + tests, étalés par étapes validées. |

Hypothèses : un développeur familier du projet ; SQLite conservé (sinon prévoir marge) ; pas de bascule vers des identifiants non séquentiels dans ce lot (recommandée ultérieurement).

---

*Rapport d'analyse remis au Directeur Technique pour validation architecturale. Aucune modification du code n'a été effectuée. Le développement ne débutera qu'après votre validation, conformément au protocole PSM2S.*
