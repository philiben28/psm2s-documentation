# Architecture — Phase 4, Lot 3 : Référentiel Prestataires (Étape A)

Date : 05/07/2026
Statut : validé DT, en cours de développement.

---

## 1. Diagnostic (rappel)

Le nom d'un prestataire est aujourd'hui dupliqué en texte libre dans
**4 modèles distincts** : `Contrat.prestataire`, `Intervention.prestataire`,
`RealisationControle.organisme`, `AnalyseEau.laboratoire`. Le prestataire
est donc, dans les faits, déjà une entité métier — simplement pas encore
modélisée comme telle.

## 2. Périmètre validé DT

- ✅ Créer l'entité `Prestataire`.
- ✅ La brancher **uniquement sur `Contrat`** dans ce lot — seul endroit où
  le besoin métier est démontré (coordonnées visibles quand un contrat
  expire).
- ✅ Documenter les 3 autres usages (`Intervention`, `RealisationControle`,
  `AnalyseEau`) comme candidats à un futur lot, sans y toucher — conforme
  à `POLITIQUE-001` (généraliser seulement quand le besoin est prouvé).
- ✅ Modèle volontairement minimal : `nom`, `contact_nom`, `telephone`,
  `email`, `adresse`, `site_web`. Rien de plus (pas de SIRET, catégories,
  certifications, historique, évaluations).

## 3. Migration en deux étapes (recommandation DT)

**Étape A (ce lot)** :
- Créer `Prestataire`.
- Ajouter `Contrat.prestataire_fk` (nullable), qui **coexiste** avec
  `Contrat.prestataire` (texte, inchangé).
- Migration de données : pour chaque `Contrat` existant, retrouver ou
  créer le `Prestataire` correspondant et renseigner `prestataire_fk`.
- Formulaires/vues utilisent déjà la FK pour afficher les coordonnées et
  pour créer/retrouver le prestataire à la saisie.
- Retour arrière trivial : `prestataire_fk` est nullable et n'affecte pas
  le fonctionnement existant si on l'ignore.

**Étape B (différée, hors périmètre de ce lot)** : suppression du champ
texte `prestataire` et éventuel renommage de `prestataire_fk`, une fois la
migration validée en production et en formation. Ne sera engagée que sur
nouvelle validation DT explicite.

## 4. Dédoublonnage à la migration

Un même prestataire peut être saisi sous plusieurs formes
(`SOCOTEC` / `Socotec` / `socotec `). Normalisation minimale, non
sophistiquée : suppression des espaces de bord, réduction des espaces
multiples, comparaison **insensible à la casse** pour retrouver un
`Prestataire` déjà créé avant d'en créer un nouveau
(`Prestataire.objects.get_or_create_normalise`). Cette même règle sert à
la fois à la migration de données et à la saisie normale (un seul point
de vérité pour la normalisation, dupliqué une fois — volontairement, dans
le fichier de migration lui-même, par convention Django : une migration
ne doit pas dépendre du code applicatif futur, qui peut changer).

## 5. Formulaires et vues (ce lot)

Pas de nouvel écran de gestion des prestataires (liste/fiche/CRUD) dans
ce lot — resterait à faire si le besoin de "cliquer depuis un contrat vers
la fiche prestataire" ou "voir tous les contrats d'un prestataire" se
confirme (piste notée, non développée ici). Pour rester minimal :
- `ContratForm` garde son champ texte `prestataire` (aucune rupture
  d'usage pour qui saisit un contrat) ; à l'enregistrement, la vue
  résout/crée automatiquement le `Prestataire` correspondant via
  `get_or_create_normalise` et renseigne `prestataire_fk`.
- La page contrat (`contrat_form.html`, mode modification) affiche un
  encart en lecture seule avec les coordonnées du `Prestataire` lié
  (téléphone, email, adresse, site web), si renseignées. C'est ce bloc qui
  livre la promesse de démonstration : un Directeur qui clique sur
  l'alerte "Contrat SOCOTEC — expire dans 10 jours" (lien direct posé en
  P4-L2) arrive sur cette page et voit immédiatement les coordonnées.

## 6. Sécurité et périmètre

Aucun changement de contrôle d'accès : `Prestataire` n'est pas rattaché à
un établissement (un même prestataire peut intervenir sur plusieurs
sites), donc pas de notion de périmètre IDOR sur ce modèle. L'accès aux
coordonnées d'un prestataire reste conditionné par l'accès au `Contrat`
qui le référence (contrôle déjà en place, `verifier_acces_etablissement`).

---

*Rédigé par le Lead Developer PSM2S, 05/07/2026.*
