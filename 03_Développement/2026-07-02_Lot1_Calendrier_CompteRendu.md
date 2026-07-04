# Compte-rendu de fin de développement — Lot 1 : Calendrier Réglementaire (vue Mois)

Date : 02/07/2026
Statut : **validé par le Product Owner** (Étape 6 du protocole).
Développement conforme au DEVELOPMENT_PROTOCOL : analyse → validation → sauvegarde → développement → vérification → validation.

---

## 1. Fichiers modifiés

| Fichier | Nature | Détail |
|---|---|---|
| `registre/views.py` | Ajout uniquement | Un bloc unique encadré par les bannières `LOT 1 — CALENDRIER RÉGLEMENTAIRE (début)/(fin)`, inséré après `_calculer_prochaine_echeance` : constantes de seuils, `_couleur_conformite()`, `_construire_grille_mois()`, vue `calendrier()` |
| `registre/urls.py` | Une ligne ajoutée | `path('calendrier/', views.calendrier, name='calendrier')` |
| `Templates/base.html` | Un lien ajouté | Entrée « Calendrier » (icône `ti-calendar`, bloc `nav_calendrier`) dans la section « Principal » de la sidebar, masquée aux prestataires |
| `Templates/registre/calendrier.html` | **Fichier créé** | Grille mensuelle, bandeau des retards, légende, navigation de mois |

Aucun modèle modifié. Aucune migration. Aucun fichier statique ajouté.
Sauvegarde préalable : `PSM2S\Sauvegardes\2026-07-02_avant_Lot1_calendrier\`.

---

## 2. Choix techniques réalisés

**Rendu 100 % serveur (option A validée).** Grille générée en Python avec le
module standard `calendar` (`monthdatescalendar`, semaines lundi → dimanche),
affichée en tableau HTML/CSS. Aucune bibliothèque JavaScript : le besoin
(pastilles colorées + lien vers la fiche) ne justifiait aucune dépendance.

**Seuils de couleur paramétrables.** Deux constantes en tête du bloc LOT 1 de
`views.py` : `SEUIL_ORANGE_JOURS = 30` et `SEUIL_ROUGE_JOURS = 7`.
Règle : vert > 30 jours ; orange entre 30 et 7 jours ; rouge < 7 jours ou
échéance dépassée. La légende du template lit ces valeurs dynamiquement :
modifier les constantes met à jour l'affichage ET la légende.

**Réutilisation systématique de l'existant.** Filtrage par rôle via
`_get_etab_ids_autorises()` (aucune logique de droits dupliquée) ; couleurs
issues des variables CSS de `base.html` (`--ok`, `--warn`, `--danger`) ;
clic vers la fiche existante `registre:modifier_controle` ; navigation de mois
par query string (`?annee=&mois=`), cohérente avec les filtres des autres pages.

**Performance.** Requêtes bornées aux dates de la grille affichée, avec
`select_related('etablissement', 'type_controle')` — deux requêtes par
affichage (grille + retards), indépendantes du nombre total de contrôles.

**Bandeau des retards permanent.** Les contrôles en retard sont affichés
au-dessus de la grille quel que soit le mois consulté : un retard ancien ne
disparaît jamais de la vue (pilier « Anticiper »).

---

## 3. Points importants pour les futurs développements

- Toute évolution du calendrier se fait dans le bloc LOT 1 de `views.py` et
  dans `calendrier.html` — aucun autre fichier n'est concerné.
- Le calcul des échéances reste centralisé dans `_calculer_prochaine_echeance()`
  (déclenché par `nouvelle_realisation` et `modifier_controle`). Le calendrier
  ne fait que lire `prochaine_echeance` : la mise à jour après validation d'un
  contrôle est donc automatique, sans code supplémentaire.
- Les statuts `pas_obligation` et `non_concerne` sont exclus du calendrier ;
  les contrôles sans `prochaine_echeance` n'y apparaissent pas (rien à placer).
- La couleur est calculée uniquement sur la date (règle PO) ; la propriété
  `est_en_retard` du modèle reste la référence pour les autres écrans.
- Si les seuils doivent un jour devenir modifiables par l'administrateur sans
  toucher au code, prévoir un petit modèle de paramètres (migration nécessaire)
  — hors périmètre actuel, les constantes suffisent.

## 4. Limites connues

- La fiche contrôle (`modifier_controle`) est réservée aux gestionnaires :
  un factotum qui clique sur un événement est redirigé vers le dashboard
  (comportement existant, non modifié). Cible du Lot 1 = Directeur et
  Responsable Sécurité, conforme à la décision PO.
- Un contrôle au statut « fait » dont l'échéance est passée (cas atypique :
  périodicité absente) apparaît en rouge dans la grille mais pas dans le
  bandeau — la règle de couleur est purement calendaire.
- Un jour très chargé allonge la cellule (pas de repli « +n autres ») ;
  acceptable au volume actuel, à prévoir si le nombre d'échéances/jour croît.
- Navigation de mois par rechargement de page (choix assumé de l'option A).
- Vérifications exécutées statiquement (environnement d'exécution indisponible
  pendant le développement) ; `python manage.py check` et le test visuel de
  `/calendrier/` ont été confiés au PO — validés.
- Aucun dépôt Git détecté dans le projet : la sauvegarde est assurée par le
  dossier `Sauvegardes\`. Recommandation forte : initialiser Git.

## 5. Recommandations pour le Lot 2

Conformément au backlog et aux décisions PO, par ordre de valeur :

1. **Vues Semaine et Jour** : même source de données, paramètre `vue=` dans la
   même URL et la même vue Django ; rendu en liste ordonnée (plus lisible
   qu'une grille pour ces granularités). Réutiliser `_couleur_conformite`.
2. **Filtres simples** : par établissement et par catégorie de contrôle
   (query string, motif identique à `controles_global`).
3. **Sources secondaires d'échéances** (versions ultérieures validées PO) :
   contrats (`date_fin`), prescriptions (`delai`), tickets (`date_cible`),
   avec pictogrammes distincts — à introduire une source à la fois.
4. **Ergonomie** : repli « +n autres » sur les jours chargés ; lien retour
   « voir dans le calendrier » depuis la fiche contrôle.
5. **Technique** : initialiser un dépôt Git avant le Lot 2 (Étape 3 du
   protocole) ; créer le fichier `Documentation/00_IA/DECISIONS.md` référencé
   par START_HERE.md mais absent, pour y consigner les décisions PO déjà
   prises (option A, seuils 30/7, périmètre contrôles seuls).

---

*Rédigé par l'équipe de développement IA — PSM2S, 02/07/2026.*
