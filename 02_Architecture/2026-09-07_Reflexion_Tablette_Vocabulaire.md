# Réflexion — PSM2S sur tablette Android & vocabulaire multi-marchés

Date : 07/09/2026
Méthode : lecture seule du code réel (`registre/models.py`, `registre/forms.py`, `registre/views.py`, `Templates/base.html` et gabarits associés). Aucune modification, aucune migration, aucune donnée touchée. Ce document sert de base de décision, pas de spécification figée.

---

## A. Analyse tablette

### A.1 — Écrans les plus utilisés sur le terrain

D'après le scénario cible (constat → ticket → intervention → clôture), les écrans concernés sont : `dashboard`/`detail_etablissement` (vue du bâtiment), `tickets`/`nouveau_ticket`/`modifier_ticket`, `interventions`/`nouvelle_intervention`/`modifier_intervention`, `ajouter_piece_jointe`, `detail_prestataire`. C'est sur ces écrans que porte l'analyse.

### A.2 — Constat technique de fond : aucune adaptation mobile n'existe aujourd'hui

Vérifié dans `Templates/base.html` (le gabarit commun à tout l'applicatif) :

- La balise `viewport` est présente (`width=device-width, initial-scale=1.0`) — c'est le seul réflexe mobile déjà en place.
- **Aucune règle `@media` nulle part dans la feuille de style commune.** La mise en page ne s'adapte à aucune largeur d'écran : c'est une disposition desktop fixe, jamais pensée pour se réorganiser.
- **La barre latérale (`.sidebar`) est fixe, 224 px, toujours visible**, sans mécanisme de repli (pas de bouton menu/hamburger, aucun script de bascule trouvé). Sur une tablette 10 pouces en portrait (~768 px de large), elle occupe near 30 % de l'écran en permanence, sur chaque page.
- **Les cibles tactiles sont sous-dimensionnées** : boutons d'action `.icon-btn-sm` et `.logout-btn` = 26 à 28 px. Les repères d'ergonomie tactile courants (Apple/Material) recommandent 44-48 px minimum. Un doigt sur tablette ratera régulièrement ces boutons.
- **Les formulaires utilisent des grilles à deux colonnes fixes** (`.form-row { grid-template-columns:1fr 1fr; }`, vu dans `modifier_intervention.html` pour date/statut) sans repli à une colonne — inconfortable en portrait.
- Les tailles de texte sont globalement petites (corps 14 px, badges/labels 11-13 px) — lisible sur écran de bureau, limite en extérieur ou avec la luminosité d'un hall d'entrée.

**Conclusion de constat** : ce n'est pas un problème de "quelques réglages à ajuster", c'est une interface qui n'a jamais été pensée en dehors du poste de travail. Le besoin exprimé — ne pas se contenter de réduire l'affichage PC — est donc justifié : réduire l'affichage actuel ne suffirait pas, il faudrait une vraie disposition adaptative (sidebar repliable, formulaires à une colonne sur petit écran, cibles tactiles agrandies).

### A.3 — Appareil photo et pièces jointes : possible, mais pas optimisé

Vérifié dans `registre/forms.py` (`PieceJointeTicketForm`) : le champ fichier est un `ClearableFileInput` standard, **sans attribut `accept` ni `capture`**. Concrètement : sur Android, l'utilisateur peut techniquement prendre une photo (le sélecteur de fichiers Android propose en général l'appareil photo parmi les options), mais ce n'est pas un accès direct — il faut ouvrir le sélecteur, puis choisir "Appareil photo" parmi plusieurs options (fichiers, galerie, etc.). Un attribut `capture="environment"` sur ce champ suffirait à lancer l'appareil photo arrière directement, en un geste. C'est une modification minime, à fort effet perçu.

### A.4 — Gap fonctionnel réel découvert, indépendant de la question tablette

En vérifiant comment un ticket est réellement créé aujourd'hui (`TicketTravauxForm`, `nouveau_ticket.html`) : le formulaire de création d'un ticket **n'expose pas le champ `TicketTravaux.description`** — seuls `établissement, titre, priorité, statut, date_cible, responsable` sont saisissables. Confirmé aussi côté modification : aucun formulaire dans tout `forms.py` n'expose ce champ. Le texte du constat (le "quoi s'est-il passé") n'est aujourd'hui saisissable nulle part dans l'interface réelle — les descriptions riches vues dans la démo ont été écrites directement en base par script, pas par un vrai formulaire.

C'est un vrai manque fonctionnel, indépendant de la tablette : le scénario cible ("ajouter une observation" au moment du constat) n'est aujourd'hui possible qu'au niveau de l'intervention (`Intervention.description`, lui bien exposé), pas au moment de la création du ticket. Ça mérite d'être traité, tablette ou pas.

### A.5 — Adaptations d'ergonomie concrètes proposées

- Sidebar repliable par défaut sur petit écran, réduite à une barre d'icônes ou masquée derrière un bouton, plutôt que 224 px fixes.
- Cibles tactiles portées à 44 px minimum sur les boutons d'action (modifier, joindre, supprimer).
- Formulaires : une seule colonne sous un certain seuil de largeur, champs plus hauts (padding vertical augmenté).
- Ajout du champ `description` au formulaire de création de ticket (cf. A.4) — utile sur tous les supports, indispensable sur tablette où le contexte se perd vite entre le constat et sa saisie.
- Attribut `capture="environment"` sur les champs fichier des tickets/interventions.
- Un bouton d'action flottant ou très visible "Nouveau ticket" accessible en permanence depuis la fiche établissement, pour minimiser les allers-retours.

### A.6 — Logique de navigation "parcours complet en peu de gestes"

Aujourd'hui, le parcours réel (fiche établissement → nouveau ticket → [pas de description possible] → liste tickets → ouvrir le ticket → nouvelle intervention → décrire/joindre) traverse plusieurs écrans distincts sans fil conducteur visuel. Une piste, sans généraliser à ce stade (juste une direction) : un parcours en une seule page-écran mobile, en étapes verticales (constat + photo → affectation → suivi), plutôt que des allers-retours entre `tickets`, `interventions` et `pièces jointes` qui sont aujourd'hui trois zones de navigation séparées dans le menu latéral.

---

## B. Analyse du vocabulaire

Classification des termes réellement présents dans le code (menus de `base.html`, `verbose_name` des modèles, intitulés de formulaires).

| Terme actuel | Statut | Alternative envisageable | Gain / Risque |
|---|---|---|---|
| Établissement | 🟠 | Site / Bâtiment | Le modèle lui-même dit déjà "Un site / bâtiment recevant du public" en commentaire — le code est prêt culturellement, l'UI ne l'est pas encore. Gain : parle immédiatement à une collectivité ou une entreprise. Risque : le mot "Établissement" a un sens juridique précis en ESMS (établissement médico-social) — à garder en synonyme contextuel plutôt qu'à supprimer. |
| Ticket travaux | 🟢 | — | Déjà générique, compris partout (facility management, IT, BTP). |
| Intervention | 🟢 | — | Terme déjà neutre. |
| Prestataire | 🟢 | — | Déjà générique. |
| Échéance | 🟢 | — | Déjà générique. |
| Document | 🟢 | — | Déjà générique. |
| Contrôle réglementaire | 🟢 | — | Confirmé générique : `type_erp`/`categorie ERP` (Type J/R/U/W, catégories 1-5) sont une classification réglementaire française applicable à tout bâtiment recevant du public, pas seulement au médico-social. |
| Correspondant local | 🟢 | — | Déjà neutre, compréhensible par tous. |
| Registre de sécurité | 🟠 | Registre technique / Registre du bâtiment | Terme réglementaire précis et valorisant en ESMS/ERP ; une entreprise privée sans obligation ERP pourrait le percevoir comme hors sujet. À garder tel quel quand `obligation_reglementaire=True`, et basculer vers une appellation plus neutre sinon (le champ existe déjà dans le modèle `Etablissement`). |
| Visite de commission | 🔴 | (rester spécifique) | Renvoie à une réalité administrative précise (commission de sécurité ERP) — se généralise mal, et le généraliser ferait perdre le sens exact pour les publics qui en ont besoin. Confirmé : à garder tel quel, avec une présentation contextuelle (afficher/masquer selon le profil). |
| Prescription | 🔴 | Réserve / Anomalie / Action corrective | Jargon de commission de sécurité, peu clair hors de ce contexte. Bon candidat à la généralisation suggérée par Phil — day-to-day une "anomalie à corriger" est un concept universel. |
| DUERP | 🔴 | (rester spécifique, en le complétant) | Obligatoire pour TOUT employeur français (pas seulement ESMS) donc déjà transversal sur le fond — mais le sigle lui-même est absent du vocabulaire courant hors monde RH/QSE. Garder le terme réglementaire exact (obligatoire de le nommer ainsi), en ajoutant un sous-titre explicite ("Évaluation des risques professionnels") pour les marchés qui ne connaissent pas le sigle. |
| Registre d'accessibilité | 🔴 | (rester spécifique) | Terme réglementaire précis (loi handicap), à conserver tel quel — se substitue mal à autre chose sans perdre le sens juridique. |
| Factotum | 🔴 | Agent technique / Technicien de maintenance | "Factotum" est daté et peu utilisé hors secteur associatif/ESMS. "Agent technique" ou "Technicien" parle à tous les marchés sans rien perdre. Bon candidat à la généralisation. |
| Directeur | 🟠 | Responsable de site / Gestionnaire | En entreprise privée ou collectivité, "Directeur d'établissement" sonne très ESMS ; "Responsable" est plus neutre. Rôle interne (`role='directeur'`), donc renommage d'affichage possible sans toucher à la mécanique des permissions. |
| Partenaires (menu) | 🟢 | — | Déjà choisi de façon neutre (cf. Phase 4, Lot 4) — bon exemple à suivre pour le reste. |

### Résumé
La majorité du vocabulaire technique (tickets, interventions, prestataires, échéances, documents, contrôle réglementaire) est déjà neutre — bonne nouvelle, la base est saine. Les points ORANGE/ROUGE se concentrent sur des termes hérités du monde ESMS pur (Factotum, Directeur, Visite de commission, Prescription, registre de sécurité) — remplaçables ou contextualisables sans toucher à un seul champ de base de données, puisqu'il s'agit presque partout d'intitulés d'affichage (`verbose_name`, labels de formulaire, menus), pas de noms de champs techniques.

---

## C. Proposition de positionnement

À partir de ce constat, PSM2S peut se présenter comme un outil de **gestion technique et opérationnelle des bâtiments**, sans renoncer à ses fonctions de sécurité/conformité — au contraire, ces fonctions deviennent un argument différenciant ("la plupart des outils de gestion technique ne couvrent pas la conformité réglementaire ; PSM2S le fait nativement").

Concrètement : un vocabulaire d'affichage à deux niveaux, pas un logiciel à trois variantes. Le cœur (modèles, permissions, logique métier) reste unique — seuls les libellés d'écran changeraient, portés par le mécanisme déjà existant du projet (`config/env.py`, personnalisation d'identité par instance, déjà utilisé pour le nom/les couleurs). Un "Directeur" resterait un `role='directeur'` en base, mais pourrait s'afficher "Responsable de site" pour une instance entreprise, sans toucher au modèle.

## D. Priorisation

**Priorité 1 — indispensable pour une bonne utilisation tablette**
- Sidebar repliable / navigation mobile.
- Cibles tactiles à 44 px minimum sur les actions.
- Formulaires en une colonne sous un certain seuil de largeur.
- Ajouter le champ `description` au formulaire de création de ticket (gap fonctionnel réel, pas seulement tablette).
- `capture="environment"` sur les champs photo/pièce jointe.

**Priorité 2 — important mais non bloquant**
- Parcours "constat complet" simplifié (moins d'allers-retours entre tickets/interventions/pièces jointes).
- Renommages d'affichage ORANGE (Établissement→Site, Directeur→Responsable, registre de sécurité→registre technique) via un mécanisme de libellés configurables, pas en dur.
- Généralisation de "Prescription" → "Anomalie/Réserve" et "Factotum" → "Agent technique".

**Priorité 3 — idées à garder pour plus tard**
- Positionnement marketing formalisé en trois déclinaisons de vocabulaire par marché (ESMS, collectivité, entreprise), au-delà du simple renommage d'écran.
- Éventuelle évolution du modèle `Prestataire` vers une distinction Contrôle/Maintenance/Fourniture (déjà discutée séparément le 03/09, non retenue pour l'instant).

---

Aucune modification effectuée. Ce document sert de support de décision commune — la suite (quoi développer réellement, dans quel ordre) reste à définir ensemble.
