# POLITIQUE-001 — Politique d'évolution Core / Variante de PSM2S

Statut : document permanent et officiel de la plateforme, au même titre
que `IA_RULES.md`, `PROC-001` et `PROC-002` (élevé au rang de référence
permanente le 04/07/2026, sur décision du Directeur Technique).
Issu de l'analyse L3.4.1 (cartographie), L3.4.2 (niveaux de
personnalisation) et L3.4.3 (règles d'évolution) — voir
`Documentation/03_Développement/2026-07-04_L3.4.1_*.md` à `L3.4.3_*.md` pour
le détail du raisonnement ayant produit cette politique.

## Portée

Ce document ne décrit **aucun mécanisme technique** (structure de
dossiers, Git, variables de configuration) — c'est l'objet de L3.4.4. Il
fixe la question à se poser **avant** toute décision technique, à chaque
nouvelle demande d'évolution, qu'elle vienne d'un client existant ou d'un
futur client.

## La règle

Face à toute nouvelle demande, appliquer cette séquence, dans cet ordre,
et s'arrêter à la première réponse positive :

1. **Paramètre ?** La demande touche-t-elle uniquement l'identité,
   l'apparence ou une information propre à l'instance (nom, logo,
   couleurs, coordonnées, domaine, identité d'envoi d'email) ?
2. **Module commun existant ?** Le besoin correspond-il à un module déjà
   présent, que ce client n'utilise pas encore mais qui répondrait à
   l'identique de ce qu'il fait pour les clients qui l'utilisent déjà ?
3. **Généralisable au Core ?** Reformulée plus largement, la demande
   apporterait-elle une valeur à d'autres clients ? Peut-elle devenir un
   nouveau paramètre, un nouveau module, ou une évolution légitime du
   Core, plutôt qu'un code réservé à un seul client ?
4. **Personnalisation métier, en dernier recours seulement.** Si, et
   seulement si, aucune des trois étapes précédentes ne s'applique.

## Qui décide

Cette politique ne crée pas de nouvelle règle de gouvernance : elle
s'applique dans le cadre déjà fixé par `IA_RULES` (§Décisions soumises à
validation).

- Étapes 1 et 2 : relèvent en général de l'autonomie du Lead Developer
  (configurer un paramètre ou activer un module existant ne touche ni le
  modèle de données, ni le périmètre fonctionnel, ni la sécurité).
- Étape 3 : dès qu'elle fait évoluer le Core (nouveau champ générique,
  nouveau type de contrôle structurant, nouveau module), elle touche le
  modèle de données et/ou le périmètre fonctionnel — validation DT requise.
- Étape 4 : touche par définition le périmètre fonctionnel pour un client
  donné — **validation DT systématique, sans exception**.

## Traçabilité

Toute demande ayant atteint l'étape 3 ou 4 est consignée dans
`DECISIONS.md`, avec la justification du parcours suivi (pourquoi les
étapes précédentes ont été écartées). Cette trace permet de vérifier, dans
la durée, que le Core n'a pas dérivé sans qu'on s'en aperçoive.

## Première question à se poser

À réception de toute demande d'évolution, la première question n'est plus
« comment la développer ? » mais **« à quelle étape de cette politique
appartient-elle ? »**.

---

## Historique

- **v1.0** (04/07/2026) : élévation au rang de document permanent, à partir
  de L3.4.3 (validé DT le 04/07/2026). Contenu inchangé par rapport à
  L3.4.3 — seul le statut du document change (référence durable plutôt que
  livrable de lot).
