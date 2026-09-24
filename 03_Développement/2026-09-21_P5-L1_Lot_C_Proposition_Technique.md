# P5-L1 — Lot C : proposition technique (pour validation DT avant développement)

Fait suite à `2026-09-21_P5-L1_Lot_C_Analyse_Architecture.md`. **Aucun
code, aucune migration.** Intègre les cinq arbitrages DT du 21/09/2026 :

1. `registre/contractualisation.py` = sous-lot **C0**, préalable.
2. Renouvellement = séquence **explicite et contrôlée**, jamais de
   bascule automatique silencieuse.
3. L'**absence** de contrat actif a un état d'interface explicite (pas
   de page vide, pas d'erreur silencieuse).
4. Toutes les routes commerciales sous **`/commercial/...`**.
5. Ergonomie établissements/bâtiments **définie** ci-dessous (§5),
   avant tout développement.

Un nouveau point fonctionnel, non couvert par les cinq arbitrages et
non tranché dans cette proposition, est signalé au §7 plutôt que
décidé implicitement.

---

## 1. Sous-lot C0 — `registre/contractualisation.py`

Module de fonctions pures, aucune vue, testable seul (même logique que
les modèles du Lot A avant leurs vues).

| Fonction | Rôle | Source |
|---|---|---|
| `perimetre_a_date(contrat, date)` | Reconstruit le périmètre (établissements, bâtiments) en rejouant les `MouvementPerimetre` du contrat jusqu'à `date` incluse. Retourne `{'etablissements': set(ids), 'batiments': set(ids)}`. | Architecture §2 |
| `tarif_mensuel(contrat, date=None)` | Montant HT/mois à `date` (défaut aujourd'hui) : `perimetre_a_date` × tarifs unitaires du contrat. Jamais stocké. | Architecture §3.2 |
| `statut_coherent(contrat)` | Compare `statut` stocké aux dates (`date_debut`, `date_fin`, `date_resiliation`) à la date du jour. Retourne un signal (pas un blocage), jamais de correction automatique. Explicitement redirigée ici depuis le modèle au Lot A. | Architecture §3.1, `models.py` ligne 1647-1650 |
| `maintenance_due(contrat, date=None)` | Montant de maintenance dû si `date` correspond à la date anniversaire du contrat. | Architecture §3.3 |
| `signal_depassement_perimetre(contrat, date=None)` | Compare le périmètre réel (`Etablissement.actif`/`Batiment.actif`) au périmètre contractuel. | Architecture §3.4 |
| `signal_gestionnaire_absent(contrat)` | `True` si `gestionnaire_contractuel` est `None` ou `is_active=False`. | Architecture §3.4 |

**Point à confirmer** (déjà relevé dans l'analyse, non tranché par les
cinq arbitrages) : `maintenance_due`/`signal_depassement_perimetre`/
`signal_gestionnaire_absent` sont-elles écrites au Lot C (fonctions
pures, sans câblage dashboard) ou entièrement différées au Lot E ? Les
deux premières fonctions (`perimetre_a_date`, `tarif_mensuel`) sont en
revanche des **prérequis stricts** de C1/C3, pas négociables dans le
séquencement. Recommandation : écrire les six fonctions ensemble au
Lot C (coût marginal faible, même fichier, mêmes tests), ne câbler sur
le dashboard qu'au Lot E — mais c'est une recommandation, pas une
décision prise ici.

**Tests C0** : reconstruction sur un historique multi-mouvements
(exemple déjà donné par Phil : 01/01 puis 01/04), tarif évolutif,
indépendance de `perimetre_a_date` vis-à-vis de l'état actuel des
objets (`Etablissement.actif`), absence de prorata (le montant ne
change qu'aux dates d'effet), `statut_coherent` signale sans jamais
lever d'exception ni modifier le contrat.

---

## 2. Routes — sous `/commercial/...` (arbitrage n°4)

| Route | Vue | Rôle |
|---|---|---|
| `/commercial/` | `commercial_accueil` | Point d'entrée : redirige vers `/commercial/contrat/<pk>/` du contrat `ACTIF` s'il existe ; sinon affiche l'état explicite « aucun contrat actif » (§4). |
| `/commercial/contrat/<int:pk>/` | `contrat_detail` | Consultation d'un contrat précis, actif ou passé — réutilisée par l'historique. Résout l'ambiguïté « objet unique sans `pk` » de l'analyse : chaque contrat a sa propre URL, comme partout ailleurs dans PSM2S. |
| `/commercial/contrat/historique/` | `contrat_historique` | Liste des contrats passés (`contrat_precedent`/`renouvellements`), chaque ligne renvoie vers `contrat_detail`. |
| `/commercial/contrat/renouveler/` | `renouvellement_form` | Crée un nouveau `ContratCommercial`. Accessible même en l'absence de tout contrat (= création du tout premier contrat, `contrat_precedent=None` — déjà permis par le modèle, pas un cas spécial à coder). Pré-remplit depuis le contrat actif s'il y en a un. |
| `/commercial/contrat/<int:pk>/activer/` | `activer_contrat` | Action explicite décrite au §3 — répond à l'arbitrage n°2. **Nouvelle vue, ne figurait pas dans la liste initiale de Phil — signalée en tant que telle.** |
| `/commercial/contrat/<int:pk>/resilier/` | `resiliation_form` | Statut `RESILIE` + date + motif, comme spécifié. |
| `/commercial/demandes/` | `demande_avenant_liste` | `demandes_avenant_visibles(user)` (Lot B), aucun changement à cette fonction. |
| `/commercial/demandes/nouvelle/` | `demande_avenant_form` | Entrée libre. Avec `?etablissement=<pk>`, pré-remplit une ligne `AJOUT`/`ETABLISSEMENT` (+ lignes bâtiments selon §5) — même vue, comportement piloté par un paramètre optionnel, pas une deuxième vue. |
| `/commercial/demandes/<int:pk>/traiter/` | `demande_avenant_validation` | Un seul écran, deux boutons de soumission (`action=valider` / `action=rejeter`) — choix d'implémentation sans enjeu fonctionnel, pas soumis à validation DT. |

**Intégration à l'existant** (déjà actée, plan de développement §7) :
`detail_etablissement.html` reçoit un lien
`/commercial/demandes/nouvelle/?etablissement=<pk>` dans son bandeau
informatif, si l'établissement est hors périmètre contractuel et que
l'utilisateur est habilité à soumettre. Aucune autre modification de
gabarit existant.

**Collision de vocabulaire** (relevée dans l'analyse) : le préfixe
`/commercial/` règle la collision d'URL avec `Contrat` (prestataire).
Recommandation maintenue pour les templates :
`Templates/registre/commercial/` (nouveau sous-dossier), pas
`Templates/registre/contrat_*.html` (déjà pris par le prestataire).

---

## 3. Renouvellement — séquence explicite et contrôlée (arbitrage n°2)

**Contrainte de départ, déjà en base depuis le Lot A** : `clean()`
interdit deux contrats `ACTIF` simultanés (`models.py` ligne 1601-1609).
`renouvellement_form` crée donc **toujours** le nouveau contrat en
`EN_ATTENTE` — jamais directement `ACTIF` (sans quoi la validation du
modèle échouerait dès que l'ancien contrat est encore actif, ce qui est
le cas normal). Le passage à `ACTIF` est un acte séparé, explicite :
`activer_contrat`.

**Deux façons de rendre cet acte « explicite et contrôlé, jamais
automatique silencieux »** — non tranchées entre elles, signalées pour
arbitrage :

- **Option A — activation groupée, en un seul geste visible.**
  `activer_contrat(pk)` affiche un écran de confirmation nommant
  explicitement les deux effets avant tout enregistrement : « Ce
  contrat va passer à ACTIF. Le contrat en cours (dates) va passer à
  EXPIRÉ. » Une seule confirmation déclenche une transaction qui écrit
  les deux changements. Rien n'est caché ni différé, mais un seul geste
  produit deux écritures.
- **Option B — deux gestes strictement séparés.** `activer_contrat(pk)`
  refuse tant qu'un autre contrat est encore `ACTIF` (message explicite
  : « Résiliez ou clôturez d'abord le contrat en cours »). L'ancien
  contrat doit être traité par `resiliation_form` (motif « fin de
  cycle » ou similaire) ou par une action `expirer_contrat` distincte,
  **avant** que l'activation du nouveau soit seulement possible. Aucune
  écriture croisée, jamais deux effets dans une seule transaction.

L'option A est plus proche de l'ergonomie déjà retenue ailleurs dans
P5-L1 (un seul écran d'impact chiffré pour la `DemandeAvenant`, pas une
succession d'étapes). L'option B est plus stricte au sens littéral de
« jamais de bascule automatique » (aucun changement n'est jamais un
effet de bord d'un autre). **Recommandation de cette proposition :
option A**, parce que l'effet reste entièrement visible et confirmé
avant écriture — mais ce n'est pas tranché ici, faute d'un critère
donné pour départager les deux lectures possibles de l'arbitrage n°2.

**Cas particulier couvert par les deux options** : le tout premier
contrat de l'instance (aucun contrat précédent) — `activer_contrat` n'a
alors rien à basculer côté ancien contrat, l'écran de confirmation ne
mentionne que l'activation elle-même.

**Aucun mécanisme automatique (cron, tâche planifiée) n'est proposé** à
la date de fin naturelle d'un contrat (`date_fin` atteinte sans
renouvellement) — le contrat reste `ACTIF` en base jusqu'à ce qu'un
admin/responsable_securite agisse. `statut_coherent` (C0) signalera cet
écart (date dépassée, statut toujours `ACTIF`) sans jamais le corriger
seul, cohérent avec la philosophie déjà actée.

---

## 4. Absence de contrat actif — état d'interface explicite (arbitrage n°3)

`commercial_accueil` (`/commercial/`) est le seul point d'entrée qui
doit gérer ce cas — les autres vues (`contrat_detail`,
`contrat_historique`) prennent un `pk` explicite et n'ont donc jamais à
deviner s'« il existe un contrat ».

Comportement proposé, différencié par rôle (cohérent avec la matrice du
Lot B) :

| Rôle | Écran affiché en l'absence de tout contrat `ACTIF` |
|---|---|
| admin / responsable_securite | Message explicite « Aucun contrat commercial actif » + bouton vers `renouvellement_form` (qui sert alors de création du premier contrat). |
| `gestionnaire_contractuel` d'un contrat non-actif (`EN_ATTENTE`/`RESILIE`) | Même message, plus un lien vers ce contrat précis (`contrat_detail`) s'il existe. Pas de bouton de création (réservé à `commercial_gestion_requis`, cohérent avec le renouvellement). |
| directeur non gestionnaire | Message informatif minimal, sans détail chiffré (rien à consulter tant qu'aucun contrat n'existe) ; pas de bouton d'action. |
| factotum / prestataire | Route déjà bloquée en amont par `gestionnaire_requis` — n'atteint jamais cet écran. |

---

## 5. Ergonomie établissements/bâtiments — définie (arbitrage n°5)

Point resté ouvert dans l'architecture technique elle-même (§5.1),
tranché ici comme demandé :

**Règle retenue** : à l'ajout d'un établissement dans une
`DemandeAvenant` (via `demande_avenant_form`), ses bâtiments **actifs**
au moment de la saisie sont **pré-ajoutés automatiquement** comme
lignes `AJOUT`/`BATIMENT` distinctes, une ligne par bâtiment — jamais
un comptage implicite. L'utilisateur voit la liste complète des lignes
proposées (1 établissement + N bâtiments) et peut **décocher** un
bâtiment avant soumission (il ne sera alors pas inclus dans la
demande). Rien n'est ajouté en base tant que la demande n'est pas
soumise : la pré-proposition est un état du formulaire, pas une
écriture.

Justification : conforme à la recommandation déjà formulée dans
l'architecture (§5.1 — « mouvements explicites, un par objet »), évite
la ressaisie manuelle systématique du cas le plus fréquent (un nouvel
établissement arrive avec ses bâtiments), et respecte la structure déjà
actée de `LigneDemandeAvenant` (une ligne réelle par objet, jamais de
raccourci implicite).

**Cas du retrait** : un `RETRAIT` d'établissement ne propose **pas**
automatiquement le retrait de ses bâtiments — l'analyse n'a trouvé
aucune règle métier validée pour ce sens inverse, et le contraindre
maintenant serait une extrapolation. L'utilisateur ajoute manuellement
les lignes `RETRAIT`/`BATIMENT` s'il le souhaite. **Signalé au §7**
comme point non couvert par les décisions existantes.

---

## 6. Vues restantes — résumé

| Vue | Décorateur/garde | Formulaire | Notes |
|---|---|---|---|
| `contrat_detail` | `gestionnaire_requis` + branche interne (`etablissements_autorises`) pour limiter les agrégats à un directeur non gestionnaire (architecture §4.1) | — (lecture seule) | Utilise C0 (`tarif_mensuel`, `statut_coherent`, signaux) |
| `contrat_historique` | `verifier_acces_gestion_contrat` sur le contrat le plus récent | — (lecture seule) | |
| `renouvellement_form` | `commercial_gestion_requis` | `ContratCommercialForm` (nouveau, `ModelForm`, mêmes conventions que `ContratForm`/`PrestataireForm` — `gestionnaire_contractuel` pré-rempli mais jamais `initial` silencieux : le champ reste visible et doit être soumis explicitement, cohérent avec architecture §4.2) | Crée toujours en `EN_ATTENTE` (§3) |
| `activer_contrat` | `commercial_gestion_requis` | Écran de confirmation, pas de `ModelForm` à proprement parler | Option A ou B, à trancher (§3) |
| `resiliation_form` | `verifier_acces_gestion_contrat` | `ContratResiliationForm` (nouveau, champs `date_resiliation`/`motif_resiliation` seulement) | |
| `demande_avenant_form` | `gestionnaire_requis` (droit opérationnel inchangé, identique à `nouveau_etablissement`) | `DemandeAvenantForm` + gestion de lignes dynamiques (`LigneDemandeAvenant`, formset ou équivalent — à préciser en développement, pas un enjeu d'architecture) | Utilise C0 pour l'écran d'impact chiffré (texte déjà rédigé par Phil, architecture §4.4) |
| `demande_avenant_liste` | `gestionnaire_requis` + `demandes_avenant_visibles` | — | Déjà entièrement fourni par le Lot B |
| `demande_avenant_validation` | `verifier_acces_gestion_contrat` sur `demande.contrat_commercial` | Pas de `ModelForm` — deux actions (`valider`/`rejeter`) sur le même écran | Transaction : validation crée un `MouvementPerimetre` par ligne (protection `OneToOneField` déjà en place, Lot A) ; rejet n'écrit que sur `DemandeAvenant` |

---

## 7. Nouveaux points signalés (non tranchés par les cinq arbitrages)

1. **Option A vs B pour `activer_contrat`** (§3) — la lecture littérale
   de « jamais de bascule automatique silencieuse » peut justifier l'une
   ou l'autre option. Recommandation formulée (A), pas décidée.
2. **Périmètre exact de C0** (§1) — `maintenance_due`,
   `signal_depassement_perimetre`, `signal_gestionnaire_absent`
   écrites au Lot C ou différées entièrement au Lot E ? Recommandation
   formulée (les écrire, ne pas les câbler), pas décidée.
3. **Retrait d'établissement et ses bâtiments** (§5) — aucune règle de
   pré-proposition automatique proposée dans ce sens, faute de règle
   métier validée ; à confirmer que c'est le comportement voulu
   (ajout manuel des lignes `RETRAIT`/`BATIMENT`) plutôt qu'un oubli.
4. **`activer_contrat` comme nouvelle vue** — ne figurait pas dans la
   liste des six fonctionnalités énoncées par Phil ; introduite ici
   comme conséquence directe de l'arbitrage n°2. Signalée explicitement
   pour confirmation, pas ajoutée silencieusement au périmètre.

---

## Séquencement proposé (inchangé dans l'esprit du découpage C0-C4 de l'analyse)

C0 (`contractualisation.py`) → C1 (`contrat_detail`,
`contrat_historique`, `commercial_accueil`) → C2 (`renouvellement_form`,
`activer_contrat`, `resiliation_form`) → C3 (`demande_avenant_form`,
`demande_avenant_liste`) → C4 (`demande_avenant_validation`). Chaque
sous-lot testé avant le suivant, comme pour les Lots A/B.

Aucune modification de code n'a été effectuée pour produire ce document.
