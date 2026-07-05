# Phase 4, Lot 1 — Tableau de bord Directeur : Architecture (synthèse)

Date : 04/07/2026
Statut : en attente de validation DT avant Développement.
Périmètre validé le 04/07/2026, étendu à 4 blocs : Score global, 5 actions
prioritaires, Échéances proches (aujourd'hui / cette semaine / en retard),
Indicateurs clés (contrôles en retard, prescriptions ouvertes, tickets
critiques, contrats à échéance).

---

## 1. Rôle de cette page dans la Vision PSM2S

C'est la page que le Directeur voit en premier, chaque jour. Elle porte à
elle seule la promesse centrale de la Vision (« comprendre sa situation en
moins de 30 secondes ») et deux des quatre piliers simultanément :
**Piloter** (score, indicateurs) et **Anticiper** (actions prioritaires,
échéances proches). C'est aussi, concrètement, l'écran qui sera montré en
premier lors d'une démonstration ou d'un premier déploiement client — son
enrichissement a un effet direct sur la valeur perçue de PSM2S.

## 2. Informations existantes réutilisées

Aucune nouvelle donnée, aucun nouveau modèle. Les 4 blocs s'appuient
intégralement sur des calculs déjà écrits et déjà utilisés ailleurs :

| Bloc | Origine du calcul |
|---|---|
| Score global (%) | `taux = nb_fait * 100 / nb_total`, déjà dans `tableau_de_bord` |
| 5 actions prioritaires | Construction `alertes` (retard puis échéance ≤ 7 jours, triée par urgence), déjà dans `tableau_de_bord`, réduite à 5 |
| Échéances proches (aujourd'hui/semaine/retard) | `ControleEtablissement.est_en_retard` et `prochaine_echeance`, déjà utilisés par le Calendrier et `tableau_de_bord` — seule la catégorisation par fenêtre (jour/semaine) est nouvelle, et c'est un simple filtre sur une donnée existante |
| Contrôles en retard / Prescriptions ouvertes / Contrats à échéance | Déjà calculés dans `tableau_de_bord` (`nb_retard`, `prescriptions_ouvertes`, `contrats_expirants`) |
| Tickets critiques | Quasi-existant : `tickets_ouverts` existe déjà dans `dashboard` et `tableau_de_bord` ; ajout d'un filtre `priorite='critique'` sur `TicketTravaux`, déjà un champ du modèle |
| Périmètre du Directeur (quels établissements) | `_get_etab_ids_autorises` / `ROLES_RESTREINTS`, déjà utilisé par `dashboard` |

Seul ajout réel : agréger ces calculs, aujourd'hui écrits pour un
affichage **par établissement puis consolidé multi-sites** (`tableau_de_bord`),
vers un affichage **consolidé sur le périmètre du Directeur** (1 à quelques
établissements). Aucune nouvelle règle métier.

## 3. Composants spécifiques au Directeur vs partageables

Constat central de cette architecture : **aucun des 4 blocs n'est
intrinsèquement spécifique au rôle Directeur.** Chacun est une fonction pure
d'un ensemble d'établissements (un score, une liste d'actions, une
catégorisation d'échéances, des compteurs). Ce qui varie selon le rôle
aujourd'hui, ce n'est pas le contenu du widget — c'est le **périmètre
d'établissements** qui l'alimente (un Directeur → ses sites ; un
Responsable/Admin → tout le patrimoine), périmètre déjà déterminé par une
primitive unique et générique (`_get_etab_ids_autorises`).

Cela confirme l'intuition du DT : la bonne cible à moyen terme est **un seul
moteur de calcul de widgets, partagé par tous les profils**, alimenté par un
périmètre variable selon le rôle — plutôt que deux pages qui dupliquent la
même logique. Ce n'est cependant **pas une décision prise dans ce lot** :
conformément à la demande du DT, la question reste ouverte.

**Ce que ce lot fait pour garder la porte ouverte, sans la décision
définitive** : extraire les 4 calculs (score, actions prioritaires,
échéances par fenêtre, compteurs) en fonctions partagées, indépendantes du
rôle appelant, prenant en paramètre un ensemble d'établissements. `dashboard`
(Directeur) et `tableau_de_bord` (Responsable/Admin) appelleront ces mêmes
fonctions avec des périmètres différents. Concrètement : ni fusion des deux
routes, ni duplication de logique — un choix réversible qui n'engage rien
sur la décision finale (une ou deux pages), qui pourra être prise plus tard
sans réécrire les calculs.

---

## Validation requise avant Développement

☐ Architecture validée / ☐ Architecture à modifier

---

*Rédigé par le Lead Developer PSM2S, 04/07/2026.*
