# P5-L1 — Organisation, contrats, périmètre et tarification
## Analyse fonctionnelle et arbitrages (reprise du 19/09/2026)

Statut : lecture seule, aucun développement. Reprend l'analyse ouverte le
17/09/2026 (interrompue au profit de P5-L0), re-vérifiée sur le code
actuel avant reprise. Persisté ici car jamais écrit en fichier la
première fois — seul un résumé en a été conservé dans `DECISIONS.md`.

---

## A. État de l'existant

- **`Etablissement`** (`registre/models.py`) : site, avec un booléen
  `actif` (« Site actif »). Pas de notion de périmètre contractuel.
- **`Batiment`** : rattaché à un `Etablissement`, avec son propre booléen
  `actif` — dont le `verbose_name` dit déjà explicitement **« Bâtiment
  actif (registre facturable) »**. C'est la seule trace actuelle, dans le
  code, d'une intention de facturation — jamais reliée à un mécanisme de
  tarification réel.
- **`Contrat`** : contrat **Prestataire** (SOCOTEC, bureau de contrôle,
  etc.), rattaché à un `Etablissement` + un `type_controle` +
  `prestataire_fk`. Objet métier totalement distinct du futur contrat
  commercial PSM2S↔client. Aucune confusion dans le code aujourd'hui —
  mais le nom `Contrat` est déjà pris, donc le futur modèle ne pourra
  pas s'appeler ainsi sans ambiguïté.
- **`Utilisateur.role`** : `admin`, `responsable_securite`, `directeur`,
  `factotum`, `prestataire`. Aucun rôle « client facturé » ou
  équivalent. Aucun modèle `Client`/`Organisation` nulle part.
- **Architecture Core/Variantes (L3.4.4, validée)** : **mono-tenant par
  instance** — un client = un déploiement, une base dédiée, aucune base
  partagée. C'est le fait le plus structurant pour ce lot (voir section D).

## B. Éléments manquants

Aucun mécanisme n'existe pour : identifier le contrat commercial
lui-même (durée d'engagement, dates, statut) ; distinguer le périmètre
contractuel (ce qui est facturé) du périmètre réel (ce qui existe dans
la base) ; historiser les avenants (ajout/retrait d'établissement ou de
bâtiment, avec date d'effet) ; calculer un tarif ; déclencher la
maintenance annuelle ; signaler un dépassement de périmètre.

## C. Risques / incohérences

- **Nom `Contrat` déjà utilisé** (voir A) — le futur objet commercial
  doit porter un autre nom, sans quoi toute discussion développeur/
  utilisateur devient ambiguë (« quel contrat ? »).
- **`Etablissement.actif` / `Batiment.actif` à vocation double
  aujourd'hui** : ce booléen mélange potentiellement deux idées
  distinctes — « ce site existe et fonctionne opérationnellement » et
  « ce site est dans le périmètre facturé ». Un établissement peut être
  opérationnellement actif (contrôles, tickets en cours) tout en étant
  sorti du périmètre contractuel (cf. règle de rétention historique déjà
  validée le 17/09 : on garde l'historique après sortie de périmètre).
  Réutiliser tel quel ce booléen pour la facturation créerait une
  confusion durable. À traiter explicitement (point 6 de la section E).
- **Mono-tenant validé (L3.4.4) change la nature du besoin** : dans un
  modèle multi-tenant classique, un objet `Client` identifie *qui*
  paie, parmi plusieurs clients partageant une base. Ici, chaque
  instance PSM2S **est déjà** dédiée à un seul client — il n'y a jamais
  qu'un seul « client » possible par base. Un modèle `Client` séparé
  serait donc redondant avec l'instance elle-même. Le vrai besoin n'est
  pas d'identifier le client, mais de tracer **les conditions
  commerciales** (durée d'engagement, tarif, périmètre facturé, statut)
  — voir proposition D.

## D. Proposition d'architecture fonctionnelle (révisée)

Compte tenu de C, la proposition du 17/09 (`Client` + `ContratClient` +
`Avenant`) est simplifiée : pas de modèle `Client` séparé (redondant en
mono-tenant). Deux objets suffisent :

1. **`ContratCommercial`** (nom provisoire, à arbitrer — point 9) : un
   contrat commercial par instance, avec historique si renouvellement.
   Champs envisagés : date de signature, date d'entrée en vigueur, durée
   d'engagement (24/36/48 mois), date d'échéance d'engagement, date
   anniversaire de maintenance, statut (voir point 7), tarif appliqué
   (dérivé du barème + durée, ou figé à la signature — à arbitrer, lié
   au point 2).
2. **`MouvementPerimetre`** (nom provisoire) : une ligne par
   ajout/retrait d'établissement ou de bâtiment au périmètre facturé,
   avec date d'effet (toujours le 1er du mois suivant, règle déjà
   validée le 17/09) et type de mouvement. Historise les avenants sans
   dupliquer un objet `Avenant` distinct — chaque ligne *est* l'avenant.
   Permet de reconstituer le périmètre facturé à une date donnée et de
   comparer périmètre contractuel vs périmètre réel (base) à tout
   instant.

Calcul du tarif : fonction pure à partir de `ContratCommercial` (durée
d'engagement → tarif établissement/mois) + comptage des lignes actives
de `MouvementPerimetre` à une date donnée (nombre d'établissements,
nombre de bâtiments) — jamais stocké en dur, toujours recalculé, pour
éviter la désynchronisation.

Rien de tout cela n'est un développement engagé ici : c'est la base de
discussion pour l'architecture technique, après arbitrage de la section E.

## E. Décisions métier restantes — à arbitrer (DT)

Pour chaque point : options envisagées + recommandation. Décision à
prendre par Phil (DT/PO).

### 1. Fin de contrat / renouvellement

- **Option A** — le renouvellement crée une nouvelle ligne
  `ContratCommercial` (historique complet de chaque engagement successif).
- **Option B** — le renouvellement prolonge la ligne existante (date
  d'échéance repoussée), une seule ligne « vivante » par instance.
- *Recommandation* : Option A — cohérent avec le principe déjà posé
  ailleurs dans PSM2S (historiser plutôt qu'écraser), et nécessaire si
  la durée d'engagement ou le tarif change au renouvellement (cf. point 2).

### 2. Changement de durée d'engagement (ex. 24 → 36 mois en cours de route)

- **Option A** — seulement possible au renouvellement (nouvelle ligne
  `ContratCommercial`, nouveau tarif applicable à partir de cette date).
- **Option B** — possible à tout moment en cours de contrat, avec effet
  au prochain 1er du mois (même règle que le périmètre).
- *Recommandation* : Option A, plus simple et cohérente avec la logique
  d'engagement (un tarif dégressif suppose un engagement tenu sur sa
  durée, pas renégocié en continu) — mais point réellement ouvert,
  dépend de ta pratique commerciale.

### 3. Résiliation anticipée

- Aucune règle validée à ce jour. Questions à trancher : pénalité ou
  non ? Bâtiments/établissements simplement sortis du périmètre (donc
  facturation qui s'arrête) ou marquage explicite « contrat résilié » ?
- *Recommandation* : traiter comme un statut explicite de
  `ContratCommercial` (point 7), pas comme un cas particulier du
  périmètre — une résiliation ferme le contrat, un retrait de périmètre
  ne le ferme pas forcément.

### 4. Modification du périmètre en cours de contrat

- Déjà cadrée le 17/09 : effet au 1er du mois suivant, pas de
  proratisation. Confirmé par la relecture du code (rien n'existe
  aujourd'hui qui s'y oppose). **Semble déjà tranché** — à confirmer
  simplement.

### 5. Gestion des établissements/bâtiments ajoutés ou retirés

- Directement couvert par `MouvementPerimetre` (proposition D). Question
  ouverte : qui a le droit de déclencher un mouvement de périmètre dans
  l'application (admin seul ? aussi responsable_securite ?) — lié au
  point 8.
- *Recommandation* : réservé à `admin`/`responsable_securite`
  (`peut_tout_voir`), jamais à un directeur d'établissement — c'est une
  décision commerciale, pas opérationnelle.

### 6. Distinction actif / inactif

- Comme relevé en C, `Etablissement.actif`/`Batiment.actif` mélangent
  aujourd'hui « fonctionne opérationnellement » et potentiellement
  « facturé ». **Décision à prendre** : garder ce booléen pour son sens
  opérationnel actuel (ne pas y toucher, POLITIQUE-001 — ne pas modifier
  hors périmètre) et faire du périmètre contractuel un concept
  **entièrement séparé**, dérivé de `MouvementPerimetre`, sans jamais
  lire ni écrire `actif` pour des raisons de facturation.
- *Recommandation* : séparation stricte, comme ci-dessus — évite qu'un
  changement administratif (désactiver un site en panne) n'affecte par
  accident la facturation, et inversement.

### 7. Statuts du contrat commercial

- Proposition de valeurs : *actif*, *résilié*, *expiré* (arrivé à
  échéance sans renouvellement), *en attente* (signé, pas encore entré
  en vigueur). Pas de statut bloquant l'usage de l'application (rappel
  de la règle déjà validée : jamais de blocage logiciel, seulement un
  signal de dépassement).
- *Recommandation* : ces 4 valeurs suffisent, sans sur-ingénierie —
  point ouvert si tu identifies un besoin de statut supplémentaire.

### 8. Visibilité du contrat selon les rôles

- Aujourd'hui, seuls `admin`/`responsable_securite` ont `peut_tout_voir`
  ; un `directeur` est scopé à ses établissements (règle E5).
- *Recommandation* : le contrat commercial et son tarif restent visibles
  uniquement à `admin`/`responsable_securite` — un directeur
  d'établissement n'a pas à voir les conditions commerciales globales de
  l'instance. Un signal « périmètre contractuel dépassé » (déjà validé,
  sans blocage) pourrait en revanche être visible plus largement si tu
  le souhaites — à confirmer.

### 9. Choix définitif du nom du modèle commercial

- `Contrat` est déjà pris (Prestataire). Candidats : `ContratCommercial`,
  `Abonnement`, `ContratClient`, `ContratPSM2S`.
- *Recommandation* : `ContratCommercial` — distingue clairement du
  `Contrat` Prestataire existant sans ambiguïté, et reste neutre
  (n'suppose pas un modèle d'abonnement mensuel plutôt qu'un engagement
  pluriannuel). Décision finale à toi.

### 10. Articulation exacte avec le contrat Prestataire

- Confirmé en A/C : `Contrat` (Prestataire) et le futur
  `ContratCommercial` (PSM2S↔client) sont deux objets **sans aucune
  relation directe** entre eux — l'un décrit une prestation externe
  achetée par le client pour un établissement (SOCOTEC, etc.), l'autre
  décrit la relation commerciale entre PSM2S et le client lui-même.
  Aucune migration ni changement requis sur `Contrat` existant.
- *Recommandation* : **point déjà tranché par la lecture du code**, rien
  à arbitrer sinon confirmer qu'aucun lien n'est souhaité (ex. afficher
  le contrat commercial sur la fiche établissement) — pure question
  d'ergonomie, pas d'architecture, à traiter plus tard si besoin.

---

*Prochaine étape : arbitrage de Phil sur les points 1, 2, 3, 5 (rôles),
6, 7, 8, 9 — les points 4 et 10 semblent déjà tranchés. Une fois
arbitrés, ouverture de l'architecture technique détaillée (avant tout
développement), conformément à la méthode validée.*
