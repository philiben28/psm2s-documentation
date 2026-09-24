# P5-L1 — Lot C1 : analyse d'architecture (consultation du contrat et historique)

Document d'analyse, préalable à la proposition technique C1 et à tout
développement. **Aucune modification de code.** Fait suite au Lot C0
(commit `06c1a4d`, 265/265 tests verts).

Portée strictement C1 : `commercial_accueil`, `contrat_detail`,
`contrat_historique` — trois vues de **consultation seule** (GET,
aucune écriture). `renouvellement_form`/`activer_contrat`/
`resiliation_form` (C2) et le workflow `DemandeAvenant` (C3/C4) restent
hors périmètre, y compris comme simples liens vers des URLs qui
n'existent pas encore (§4).

**Rien ci-dessous ne rouvre les cinq arbitrages déjà tranchés** (C0
préalable — acquis, commité ; séquence de renouvellement explicite —
hors périmètre de C1 ; état explicite sans contrat actif — repris tel
que déjà proposé, précisé au §3 ; routes sous `/commercial/...` —
reprises telles quelles ; ergonomie bâtiments — hors périmètre de C1,
concerne C3). Seules les questions propres à l'interface et au
comportement de C1 sont posées.

---

## 1. Rappel de ce qui est déjà acquis (sources, pas de nouvelle décision)

- **Modèles** : `ContratCommercial` (Lot A, `models.py` lignes
  1522-1651), distinct de `Contrat` (prestataire, Phase 4) — aucune
  vue C1 ne touche à `Contrat`.
- **Permissions** (Lot B, commit `31a0fdf`) : `gestionnaire_requis`
  (existant, admin/responsable_securite/directeur),
  `verifier_acces_gestion_contrat(user, contrat)` (redirection, pas
  Http404), `etablissements_autorises(user)`.
- **Calcul** (Lot C0, commit `06c1a4d`) : `perimetre_a_date`,
  `tarif_mensuel`, `statut_coherent` — disponibles dans
  `registre/contractualisation.py`, aucune n'a encore d'appelant.
- **Matrice de consultation** (architecture technique §4.1, déjà
  validée) : champs globaux du contrat (durée, dates, statut, tarifs
  unitaires, maintenance unitaire) visibles par
  admin/responsable_securite/gestionnaire/directeur non gestionnaire —
  **identiques quel que soit l'établissement**, donc rien à cacher à
  ce niveau. Agrégats sur l'ensemble du périmètre (nombre total
  d'établissements/bâtiments, montant mensuel total) réservés à
  admin/responsable_securite. Un directeur non gestionnaire voit en
  plus une vue scopée à son seul périmètre (ses établissements : sont-
  ils dans le périmètre contractuel, depuis quand, combien de leurs
  bâtiments, part de la facture totale que représente son
  établissement).
- **Signaux** (architecture §3.4, déjà validée) : dépassement de
  périmètre et absence de gestionnaire actif, tous deux « réservés à
  l'affichage admin/responsable_securite ».
- **Routes proposées** (Lot C, proposition technique §2, jamais
  individuellement validées ligne à ligne mais conformes à l'arbitrage
  « sous `/commercial/...` ») : reprises telles quelles ci-dessous,
  §4.

---

## 2. `contrat_detail` — contenu par rôle

Décorateur : `gestionnaire_requis` (exclut factotum/prestataire,
inchangé). Branche interne pour différencier l'affichage — pas un
nouveau mécanisme de permission, un simple test sur
`request.user.peut_tout_voir` / appartenance comme
`gestionnaire_contractuel` du contrat affiché.

| Bloc affiché | admin / responsable_securite | `gestionnaire_contractuel` du contrat | directeur non gestionnaire |
|---|---|---|---|
| Champs globaux (durée, dates, statut, tarifs unitaires, maintenance unitaire) | Oui | Oui | Oui (architecture §4.1, déjà acquis) |
| Signal `statut_coherent` | Oui | **Point ouvert — voir §5.1** | Non (signaux réservés admin/responsable, §3.4) |
| Agrégats globaux (nb établissements/bâtiments total, montant mensuel total via `tarif_mensuel`) | Oui | Oui (matrice §4 : « accès intégral ») | Non, jamais (§4.1, explicite) |
| Vue scopée à son propre périmètre (ses établissements dans le périmètre, depuis quand, part de facture) | — (déjà couvert par les agrégats) | — (déjà couvert par les agrégats) | Oui — seule information chiffrée qui lui est montrée |

La colonne « vue scopée » pour un directeur non gestionnaire se calcule
avec `perimetre_a_date(contrat, aujourd'hui)` filtré sur
`etablissements_autorises(request.user)`, et sa part de facture par un
simple produit (nombre de ses établissements/bâtiments dans le
périmètre × tarifs unitaires du contrat, champs déjà publics pour lui)
— aucune nouvelle fonction de calcul nécessaire, C0 suffit.

**Historique des contrats précédents** : un lien vers
`contrat_historique` est affiché uniquement si l'utilisateur y a accès
(cf. §3) — pas de lien mort.

---

## 3. `contrat_historique` — accès et contenu

Liste des `ContratCommercial` reliés par `contrat_precedent`/
`renouvellements` (déjà navigable depuis le Lot A, aucune nouvelle
relation nécessaire), du plus récent au plus ancien. Chaque ligne
renvoie vers `contrat_detail` (même vue que pour le contrat actif —
aucune duplication de template pour un contrat historique).

**Question propre à C1, non couverte par l'architecture existante** :
`verifier_acces_gestion_contrat` prend un contrat précis en paramètre.
Contre **quel** contrat faut-il vérifier l'accès à la vue *liste* (qui
n'a pas de contrat unique en paramètre d'URL) ? Deux cas déjà couverts
par construction, un troisième réellement ouvert :
- S'il existe un contrat `ACTIF` : vérifier contre lui — un
  gestionnaire du contrat courant a accès à tout l'historique qui mène
  jusqu'à lui (cohérent avec « le pouvoir contractuel porte sur le
  contrat, pas sur un établissement », déjà tranché).
- S'il n'existe aucun contrat actif mais qu'un contrat `EN_ATTENTE` ou
  `RESILIE` le plus récent existe : vérifier contre celui-là (son
  gestionnaire désigné garde la visibilité sur ce qui a précédé).
- **S'il n'existe strictement aucun `ContratCommercial`** (tout premier
  contrat jamais créé) : `contrat_historique` n'a rien à montrer.
  Faut-il alors le rendre accessible seulement à
  admin/responsable_securite (pas de gestionnaire désigné nulle part),
  ou rediriger vers `commercial_accueil` (§4) puisqu'il n'y a rien à
  historiser ? Recommandation de cette analyse : rediriger vers
  `commercial_accueil`, qui gère déjà explicitement le cas « aucun
  contrat » — évite un écran « historique » vide et sans objet.

---

## 4. `commercial_accueil` — état explicite sans contrat actif

Repris du Lot C (proposition technique §4), affiné ici pour C1
uniquement (retrait de toute référence à une action d'écriture,
puisque C2 n'existe pas encore) :

| Rôle | Aucun `ContratCommercial` n'existe jamais | Un contrat existe mais aucun n'est `ACTIF` (`EN_ATTENTE`/`RESILIE`/`EXPIRE` le plus récent) |
|---|---|---|
| admin / responsable_securite | Message : « Aucun contrat commercial n'a encore été créé. » | Message : « Aucun contrat actif. Dernier contrat connu : [lien `contrat_detail`]. » |
| `gestionnaire_contractuel` du dernier contrat connu | (n'existe pas dans ce cas — aucun contrat, aucun gestionnaire) | Même message, avec le lien vers son contrat |
| directeur non gestionnaire | Message informatif minimal, sans lien | Même message informatif minimal |
| factotum / prestataire | Route déjà bloquée par `gestionnaire_requis`, n'atteint jamais cet écran | idem |

**Changement volontaire par rapport à la proposition technique
initiale** : le lien « créer le premier contrat »/« renouveler » vers
`renouvellement_form` (C2) est **retiré** de cette version — cette URL
n'existera pas tant que C2 n'est pas développé, et l'ajouter maintenant
produirait un lien mort ou une erreur de résolution d'URL
(`NoReverseMatch`). Le lien sera ajouté au moment de C2, pas avant —
cohérent avec la discipline déjà suivie sur tous les lots précédents
(ne jamais référencer par avance un objet qui n'existe pas encore).

---

## 5. Points propres à C1 restant à trancher

### 5.1 Un gestionnaire non-admin voit-il les signaux ?

`statut_coherent` (C0) est disponible ; l'architecture (§3.4) réserve
les signaux à « l'affichage admin/responsable_securite » **au sens
strict du rôle**, sans mentionner explicitement le
`gestionnaire_contractuel` — alors que la même architecture (§4, table
de permissions) accorde par ailleurs au gestionnaire un accès
qualifié d'« intégral » sur son contrat. Les deux formulations ne se
contredisent pas frontalement (aucune n'a été écrite en pensant à
l'autre), mais elles ne donnent pas la même réponse à une question
concrète que C1 doit trancher pour construire son template. Deux
lectures possibles :
- **Lecture stricte** : signaux réservés littéralement à
  admin/responsable_securite, jamais au gestionnaire même s'il est
  directeur.
- **Lecture par cohérence avec §4** : le gestionnaire ayant un accès
  intégral à son contrat, il voit aussi les signaux qui le concernent.

Recommandation de cette analyse : lecture par cohérence — un
gestionnaire directeur, chargé explicitement de la bonne tenue de son
contrat, a besoin du même signal qu'un admin pour agir (ex. demander
lui-même un renouvellement si `statut_coherent` signale un écart). Mais
ce n'est pas tranché ici.

### 5.2 `contrat_historique` sans aucun contrat existant (§3)

Recommandation formulée (rediriger vers `commercial_accueil`), non
tranchée formellement.

### 5.3 Pagination de l'historique

Non retenue comme un point à trancher : le rythme des contrats
commerciaux (24 à 48 mois d'engagement) ne produit qu'une poignée de
lignes sur plusieurs années. Signalé pour mémoire, pas une vraie
question.

---

## 6. Routes et templates proposés (repris du Lot C, non modifiés)

| Route | Vue | Décorateur |
|---|---|---|
| `/commercial/` | `commercial_accueil` | `gestionnaire_requis` |
| `/commercial/contrat/<int:pk>/` | `contrat_detail` | `gestionnaire_requis` + branche interne (§2) |
| `/commercial/contrat/historique/` | `contrat_historique` | `verifier_acces_gestion_contrat` sur le contrat déterminé au §3 |

Templates proposés, sous un sous-dossier dédié pour éviter toute
confusion avec le contrat prestataire (déjà recommandé au Lot C) :
`Templates/registre/commercial/accueil.html`,
`Templates/registre/commercial/contrat_detail.html`,
`Templates/registre/commercial/contrat_historique.html`.

---

## 7. Tests à prévoir pour C1

- `commercial_accueil` : les quatre combinaisons du tableau §4 (aucun
  contrat jamais créé / dernier contrat non actif, × rôle habilité/non
  habilité) ; aucun lien vers une URL C2 dans le HTML rendu (test de
  non-régression explicite, pour éviter qu'un développement futur en
  réintroduise un par erreur avant que C2 existe).
- `contrat_detail` : contenu exact par rôle (§2, quatre lignes du
  tableau) ; un directeur non gestionnaire ne voit jamais les
  agrégats globaux ; un directeur hors périmètre de l'établissement
  concerné par une ligne de périmètre ne la voit pas dans sa « vue
  scopée ».
- `contrat_historique` : chaîne `contrat_precedent` affichée dans le
  bon ordre ; accès refusé (redirection) à un directeur non
  gestionnaire ; comportement en l'absence de contrat (§3, une fois
  tranché) ; lien depuis chaque ligne vers le bon `contrat_detail`.
- Non-régression : suite complète rejouée, `manage.py check`,
  `makemigrations --check --dry-run` — même discipline que les lots
  précédents (aucun changement de modèle attendu pour C1).

---

## Points nécessitant un arbitrage DT avant la proposition technique C1

1. Un `gestionnaire_contractuel` non-admin voit-il les signaux de
   `statut_coherent` sur son propre contrat ? (§5.1)
2. Comportement de `contrat_historique` quand aucun `ContratCommercial`
   n'existe jamais — redirection vers `commercial_accueil`,
   recommandée mais non tranchée (§3, §5.2).

Aucune modification de code n'a été effectuée pour produire ce document.
