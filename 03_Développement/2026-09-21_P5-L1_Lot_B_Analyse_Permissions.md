# P5-L1 — Lot B : analyse des permissions existantes et matrice cible

Document d'analyse, préalable au développement du Lot B. **Aucune
modification de code, aucune migration.** Conformément à la méthode
suivie depuis le début de P5-L1 : analyse → arbitrage DT → seulement
ensuite développement.

Rappel du périmètre du Lot B (§10 du plan de développement) :
`commercial_gestion_requis`, `verifier_acces_gestion_contrat`, et le
tranchage du point de permission resté ouvert au §6 du plan. Rien de
visible dans l'application à l'issue de ce lot (pas encore de vue).

---

## 1. État des lieux — système de permissions actuel

Fichiers vérifiés : `registre/permissions.py` (283 lignes, lu
intégralement), `registre/models.py` (`Utilisateur`,
`EtablissementUtilisateur`).

Deux mécanismes distincts coexistent, avec des comportements de refus
différents — confirmé par lecture directe du code (déjà relevé au plan
de développement, redonné ici car c'est le socle de tout le Lot B) :

### 1.1 Contrôle par rôle statique → **redirection**

`acces_requis(*roles)` (ligne 17) : vérifie `request.user.role`, sinon
`redirect('registre:dashboard')`. Jamais de 404, jamais de 403.

Dérivés existants, tous construits sur ce même décorateur :
- `admin_requis` — admin seul.
- `gestionnaire_requis` (ligne 39) — admin, responsable_securite,
  directeur. Utilisé aujourd'hui par `nouveau_etablissement`,
  `nouveau_contrat`, `modifier_contrat`, `supprimer_contrat`, etc.
- `operateur_requis` (ligne 43) — tous sauf prestataire.
- `referentiel_partenaires_requis` (ligne 47) — admin, responsable_
  securite seuls, **pas directeur**. Créé au lot P4-L5 pour réserver la
  modification du référentiel Prestataire partagé. C'est le précédent
  exact du futur `commercial_gestion_requis` : même forme (deux rôles,
  directeur explicitement exclu), même finalité (protéger une donnée
  partagée entre établissements, pas un objet propre à un établissement).
- `factotum_niveau_requis(niveau_min)` (ligne 61) — variante paramétrée,
  hors sujet pour ce lot.

### 1.2 Contrôle par objet/périmètre → **Http404**

`verifier_acces_etablissement` (ligne 139) et `get_etablissement_ou_404`
(ligne 152) : vérifient que l'établissement pointé par l'URL appartient
au périmètre de l'utilisateur (`_get_etab_ids_autorises`, définie dans
`views.py`, seule source de vérité). En cas de refus : `Http404`,
explicitement pour ne pas révéler l'existence d'un objet hors périmètre
(commentaire du code, ligne 145-149).

Même famille déclinée pour Prestataire : `get_prestataire_ou_404`
(ligne 205) — 404 si aucun contrat visible ne relie l'utilisateur à ce
prestataire, sauf `peut_tout_voir`.

**Point déjà établi (plan de développement, §6)** : ces deux
mécanismes ne sont pas interchangeables. Le premier répond à « ce rôle
a-t-il le droit de faire cette action, en général ? » (redirection). Le
second répond à « cet objet précis appartient-il au périmètre de cet
utilisateur ? » (404, pour ne rien révéler). Confondre les deux serait
une régression de cohérence, pas une simplification.

### 1.3 Rôles et propriétés utilisateur (`registre/models.py`)

- `Utilisateur.ROLE_CHOICES` : `admin`, `responsable_securite`,
  `directeur`, `factotum`, `prestataire` — cinq rôles, aucun rôle
  commercial séparé n'existe ni n'est prévu (le rôle reste le même,
  seule l'appartenance au champ `gestionnaire_contractuel` d'un contrat
  précis change la portée d'un directeur ou d'un responsable donné).
- `peut_tout_voir` (ligne 78) : `admin`/`responsable_securite`/
  superuser. Le directeur en a été explicitement retiré (E5,
  02/07/2026) — rappel utile car `ContratCommercial` reprendra la même
  logique de périmètre restreint pour un directeur non gestionnaire.
- `EtablissementUtilisateur` (ligne 194) : rattachement utilisateur ↔
  établissement, source du périmètre d'un directeur. Aucun champ, table
  ou mécanisme de rattachement contractuel n'existe aujourd'hui —
  entièrement porté par le nouveau champ
  `ContratCommercial.gestionnaire_contractuel` (Lot A, déjà en base).

### 1.4 Ce qui n'existe pas encore

Vérifié par recherche dans `registre/views.py` : aucune référence à
`ContratCommercial`, `DemandeAvenant`, `MouvementPerimetre` ou à une
fonction `*_gestion_contrat*` — le Lot A n'a touché que les modèles.
Le Lot B part donc d'une feuille blanche pour les primitives de
permission, mais s'appuie exclusivement sur des patrons déjà éprouvés
(aucun mécanisme nouveau à inventer).

---

## 2. Ce qui doit rester strictement inchangé

Rappel du principe déjà acté (droit opérationnel ≠ pouvoir contractuel,
DECISIONS.md, arbitrages P5-L1) et à respecter impérativement dans le
Lot B :

- `nouveau_etablissement` reste `@gestionnaire_requis`
  (admin/responsable_securite/directeur) — **inchangé**. Un directeur
  garde l'intégralité de son droit opérationnel actuel.
- Soumettre une `DemandeAvenant` suit le même périmètre que
  `nouveau_etablissement` — un directeur peut toujours déclencher une
  demande pour son propre établissement.
- Aucune permission existante sur les objets déjà en production
  (Etablissement, Contrat prestataire, Prestataire, etc.) n'est
  touchée par ce lot.

Le Lot B n'ajoute des restrictions que sur des objets **nouveaux**
(`ContratCommercial`, `DemandeAvenant` côté validation) — il ne retire
aucun droit déjà accordé ailleurs.

---

## 3. Nouveaux besoins de permission introduits par le Lot A

Quatre actions distinctes nécessitent une décision de permission,
identifiées à partir des modèles réellement créés en Lot A
(`registre/models.py`, lignes 1522-1854) :

1. **Consulter le `ContratCommercial` actif** — accès différencié selon
   le rôle (intégral pour admin/responsable_securite/gestionnaire ;
   scopé au périmètre pour un directeur non gestionnaire, cf. §4.1 de
   l'architecture technique).
2. **Assigner/modifier le `gestionnaire_contractuel`** — réservé à
   admin/responsable_securite (architecture §4.2, point déjà tranché
   par Phil le 19/09/2026).
3. **Valider ou rejeter une `DemandeAvenant`** — réservé à
   admin/responsable_securite/`gestionnaire_contractuel` **du contrat
   concerné** (pas un droit de rôle pur : dépend de la donnée
   `gestionnaire_contractuel` du `ContratCommercial` lié).
4. **Consulter la liste des `DemandeAvenant`** — intégrale pour
   admin/responsable_securite/gestionnaire ; scopée au périmètre
   d'établissements pour un directeur (même logique que partout
   ailleurs).

Aucune action supplémentaire de permission n'est nécessaire pour
`MouvementPerimetre` : ce modèle n'est jamais créé ni consulté
directement par une interface (rappel modèle, ligne 1770-1777) — sa
consultation passera par l'historique du contrat (Lot C), pas par un
accès direct nécessitant sa propre permission.

---

## 4. Matrice cible

| Action | admin | responsable_securite | `gestionnaire_contractuel` du contrat concerné | directeur non gestionnaire | factotum / prestataire |
|---|---|---|---|---|---|
| Consulter le contrat commercial (champs globaux : durée, dates, statut, tarifs unitaires) | Oui | Oui | Oui | Oui | Non |
| Consulter les agrégats globaux (total établissements/bâtiments, montant total) | Oui | Oui | Oui | **Non** | Non |
| Consulter sa propre part du périmètre/facturation | Oui | Oui | Oui | Oui (son propre périmètre uniquement) | Non |
| Assigner/changer le `gestionnaire_contractuel` | Oui | Oui | Non (sauf s'il est aussi admin/responsable) | Non | Non |
| Créer un établissement (droit opérationnel, inchangé) | Oui | Oui | — (dépend du rôle réel) | Oui | Non |
| Soumettre une `DemandeAvenant` | Oui | Oui | — (dépend du rôle réel) | Oui | Non |
| Consulter la liste des `DemandeAvenant` | Oui, toutes | Oui, toutes | Oui, toutes | Limitée à ses établissements | Non |
| Valider une `DemandeAvenant` | Oui | Oui | Oui, sur ce contrat uniquement | Non | Non |
| Rejeter une `DemandeAvenant` | Oui | Oui | Oui, sur ce contrat uniquement | Non | Non |
| Créer un `MouvementPerimetre` directement | **Personne, aucune interface** | | | | |

Cette matrice reprend, sans modification, celle déjà validée dans
l'architecture technique (§4 et §4.2) — le Lot B n'introduit aucune
règle métier nouvelle, il traduit une matrice déjà actée en primitives
de code.

---

## 5. Primitives à créer (description, pas d'implémentation)

Pour rester strictement dans le rôle d'analyse de ce document, les
primitives suivantes sont décrites par leur rôle et leur patron, sans
code :

- **`commercial_gestion_requis`** (décorateur de vue) — même forme que
  `referentiel_partenaires_requis` : `acces_requis('admin',
  'responsable_securite')`. Couvre l'action « assigner un gestionnaire
  contractuel ». Patron **redirection** (décorateur de rôle statique,
  famille §1.1) — non ambigu, pas de contradiction possible sur cette
  primitive précise.
- **`verifier_acces_gestion_contrat(user, contrat)`** — fonction de
  vérification portant sur une donnée du contrat
  (`gestionnaire_contractuel`), pas sur un rôle statique seul. Logique :
  autoriser si `user.role in ('admin', 'responsable_securite') or
  user.is_superuser or contrat.gestionnaire_contractuel_id == user.id`.
  **Patron de refus non tranché — voir §6 ci-dessous.**
- **Fonction de scope pour la consultation d'un directeur non
  gestionnaire** — équivalent, pour `ContratCommercial`, de
  `etablissements_autorises`/`get_etablissement_ou_404` : restreint
  l'affichage aux champs globaux + au périmètre propre du directeur
  (§4.1 de l'architecture technique), sans jamais exposer les agrégats
  globaux.

---

## 6. Point non tranché — à arbitrer avant de coder le Lot B

**`verifier_acces_gestion_contrat` doit-il refuser par redirection ou
par `Http404` ?**

Ce point figurait déjà explicitement dans les « décisions restantes »
du plan de développement du 21/09/2026 et n'a pas été retranché depuis
dans `DECISIONS.md` — il reste donc ouvert à ce jour, distinct du
correctif 404 déjà traité (rattachement du créateur d'établissement,
21/09/2026, qui portait sur un tout autre mécanisme :
`get_etablissement_ou_404`, pas sur ce futur `verifier_acces_gestion_contrat`).

Les deux options se défendent, sans qu'aucune ne s'impose par simple
lecture du code existant :

- **Redirection** (cohérent avec les décorateurs de rôle, §1.1) :
  l'existence d'un `ContratCommercial` n'est un secret pour personne —
  contrairement à un établissement hors périmètre, ce n'est pas un
  objet dont il faut cacher l'existence. Un directeur non gestionnaire
  sait déjà qu'un contrat commercial existe (il en voit les champs
  globaux, §4.1). Recommandation déjà formulée dans le plan de
  développement, pour cette raison.
- **`Http404`** (cohérent avec `verifier_acces_etablissement`, §1.2) :
  la fonction porte sur un objet précis résolu depuis l'URL
  (`contrat`), même forme que `verifier_acces_etablissement` — au nom
  de la cohérence de forme, pas de contenu à cacher.

**Recommandation maintenue pour ce document** : redirection — la
justification tient à ce qui doit être caché (rien, ici) plutôt qu'à
la forme de la fonction. Mais ce choix conditionne directement
l'écriture des tests du Lot B (§8 du plan de développement) : à
trancher explicitement par Phil avant tout développement du Lot B,
même si ce n'est qu'une ligne de décision.

---

## 7. Fichiers concernés (vérifiés, pour le futur développement du Lot B)

- `registre/permissions.py` — ajout de `commercial_gestion_requis` et
  `verifier_acces_gestion_contrat`, à la suite des sections existantes,
  même style de commentaire d'en-tête que les sections « RÉFÉRENTIEL
  DES PARTENAIRES » et « MODULES ACTIVABLES » déjà en place.
- `registre/tests.py` — nouvelle classe de tests dédiée. Vérifié :
  aucune classe `PermissionsTests` générique n'existe ; la convention
  du projet est une classe `*AccesTests` par module, construite sur
  `BaseAccesEtablissement` (ligne 34) ou une de ses sous-classes (ex.
  `ContratAccesTests`, ligne 551 — le précédent le plus proche, déjà
  nommé « Contrat » bien que pour le Prestataire, pas la
  contractualisation). Le Lot B suivra ce même patron, sans vue à
  tester pour l'instant : les fonctions de permission seront appelées
  directement, comme le service `EnvHelperTests`/`ModuleActifHelperTests`
  le font déjà pour des fonctions de bas niveau sans vue associée.
- `registre/models.py` — **aucune modification prévue** dans ce lot
  (déjà complet depuis le Lot A).
- `registre/views.py` — **aucune modification dans ce lot** : aucune
  vue commerciale n'existe encore (confirmé §1.4), les primitives sont
  écrites avant d'avoir un appelant, comme le Lot A l'a fait pour les
  modèles avant les vues.

---

## Aucune modification de code effectuée

Ce document est une analyse. Aucun fichier de `Code-Source` n'a été
modifié pour le produire.
