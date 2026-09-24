# P5-L1 — Lot B : proposition technique (pour validation DT avant développement)

Fait suite à `2026-09-21_P5-L1_Lot_B_Analyse_Permissions.md`. Document de
proposition précise, toujours **aucun code, aucune migration**. À valider
avant tout développement du Lot B.

---

## Préalable — décision à prendre avant de valider cette proposition

Un désaccord existe entre deux documents déjà produits, tous deux datés
du 19-21/09/2026, sur le comportement de refus de
`verifier_acces_gestion_contrat` :

- **Architecture technique** (§4.2, validée le 21/09/2026) : « fonction
  dédiée `verifier_acces_gestion_contrat`, résolue contre l'objet,
  **même famille que `verifier_acces_etablissement`** » — c'est-à-dire
  la famille qui lève `Http404`.
- **Plan de développement** (§6 et « décisions restantes », même jour) :
  signale le point comme **non tranché**, avec une recommandation en
  sens inverse (redirection), au nom de la cohérence avec les
  décorateurs de rôle plutôt qu'avec la forme de la fonction.

Ces deux documents n'ont pas été écrits en confrontation l'un avec
l'autre — le second a soulevé un doute après que le premier ait déjà
tranché implicitement par sa formulation. **Ce point doit être arbitré
explicitement avant validation de cette proposition**, car il détermine
la signature de la fonction (§1) et la moitié des tests de refus (§3).
Les deux sections ci-dessous sont donc écrites en présentant les deux
variantes, pas une seule.

---

## 1. Fonctions à ajouter dans `registre/permissions.py`

| Fonction | Type | Rôle | Emplacement proposé |
|---|---|---|---|
| `commercial_gestion_requis` | Décorateur de vue | `acces_requis('admin', 'responsable_securite')` — copie littérale de `referentiel_partenaires_requis` (ligne 47). Refuse par **redirection** vers `registre:dashboard` (aucune ambiguïté sur cette fonction précise). | Nouvelle section après « RÉFÉRENTIEL DES PARTENAIRES » (ligne 186), avant « MODULES ACTIVABLES ». |
| `gestion_contrat_autorisee(user, contrat)` | Fonction bool, non levante | Retourne `True` si `user.is_superuser` ou `user.role in ('admin', 'responsable_securite')` ou `contrat.gestionnaire_contractuel_id == user.id`. Miroir non-levant de `acces_etablissement_autorise` (ligne 128) — utile pour un affichage conditionnel dans un template (ex. bouton « Valider » visible seulement si autorisé). | Même nouvelle section. |
| `verifier_acces_gestion_contrat(user, contrat)` | Fonction de garde | Appelle `gestion_contrat_autorisee`. **Variante A (si Http404 retenu)** : lève `Http404` en cas de refus, miroir strict de `verifier_acces_etablissement` (ligne 139). **Variante B (si redirection retenue)** : ne peut pas suivre exactement le même patron qu'une fonction interne — une redirection doit être renvoyée par la vue elle-même. Dans ce cas la fonction se limite à `gestion_contrat_autorisee` (déjà listée ci-dessus) et chaque vue écrit `if not gestion_contrat_autorisee(request.user, contrat): return redirect('registre:dashboard')` — pas de fonction `verifier_...` séparée, pour ne pas dupliquer un mécanisme qui n'existe pas ailleurs sous cette forme. | Même nouvelle section. |
| `demandes_avenant_visibles(user)` | Fonction utilitaire (queryset) | Retourne le queryset de `DemandeAvenant` visible : toutes pour admin/responsable_securite/superuser ; pour un directeur, restreint aux demandes dont `contrat_commercial.gestionnaire_contractuel_id == user.id` **ou** dont au moins une `LigneDemandeAvenant` porte sur un établissement de son périmètre (`etablissements_autorises`). Même esprit que `contrats_prestataire_visibles` (ligne 189, précédent direct pour ce type de fonction). | Même nouvelle section. |

**Rien d'autre n'est proposé.** Pas de nouveau rôle dans `ROLE_CHOICES`,
pas de nouveau champ sur `Utilisateur` — conforme à l'analyse du §1.3
du document précédent (l'habilitation contractuelle est entièrement
portée par `ContratCommercial.gestionnaire_contractuel`, jamais par le
rôle).

---

## 2. Vues qui utiliseront ces fonctions

Aucune de ces vues n'est développée dans le Lot B (elles appartiennent
aux Lots C et D). Cette section sert à valider que les fonctions
proposées au §1 couvrent exactement les besoins déjà identifiés dans le
plan de développement (§7 — templates déjà listés), avant de les coder
sans destinataire réel.

| Vue future (nom proposé) | Lot | Fonction(s) de permission utilisée(s) | Justification |
|---|---|---|---|
| `contrat_detail` | C | `@gestionnaire_requis` (inchangé, existant) + branche interne utilisant `etablissements_autorises` (existante) pour limiter les agrégats à un directeur non gestionnaire | Consultation ouverte à admin/responsable/gestionnaire/directeur (§4 matrice) — aucune nouvelle fonction de blocage nécessaire, seulement un filtrage d'affichage déjà outillé. |
| `contrat_historique` | C | `verifier_acces_gestion_contrat` (ou `gestion_contrat_autorisee` + redirection manuelle, selon variante retenue) | Réservé à admin/responsable_securite/gestionnaire du contrat (architecture §4.3) — un directeur non gestionnaire ne doit pas y accéder, alors que `@gestionnaire_requis` seul l'autoriserait à tort. |
| `renouvellement_form` | C | `@commercial_gestion_requis` | Réassignation du `gestionnaire_contractuel` **exigée** à chaque renouvellement (architecture §4.2) — réservé strictement à admin/responsable_securite, jamais au gestionnaire sortant lui-même. |
| `resiliation_form` | C | `verifier_acces_gestion_contrat` | « Modification du contrat » ouverte au gestionnaire du contrat concerné (matrice §4), pas seulement à admin/responsable_securite — contrairement au renouvellement. |
| `demande_avenant_form` (soumission) | D | `@gestionnaire_requis` (inchangé, identique à `nouveau_etablissement`) | Droit opérationnel, non touché par le Lot B (rappel §2 du document d'analyse). |
| `demande_avenant_liste` | D | `@gestionnaire_requis` (entrée) + `demandes_avenant_visibles(user)` (filtrage du queryset) | Directeur limité à son périmètre, admin/responsable/gestionnaire voient tout (matrice §4). |
| `demande_avenant_validation` (valider/rejeter) | D | `verifier_acces_gestion_contrat` (ou équivalent redirection) | Seuls admin/responsable_securite/gestionnaire du contrat concerné peuvent valider ou rejeter (matrice §4). |

---

## 3. Tests à ajouter dans `registre/tests.py`

Une nouvelle classe, `PermissionsContractualisationTests(TestCase)`
(pas de vue à tester — appels directs aux fonctions, comme
`EnvHelperTests`/`ModuleActifHelperTests`, déjà identifié dans le
document d'analyse §7). Fixture : réutiliser `BaseContractualisation`
déjà créée au Lot A (admin, directeur, etab, batiment) et lui ajouter
un `responsable_securite`, un deuxième directeur (pour vérifier
l'exclusion d'un directeur tiers) et un `ContratCommercial` avec
`gestionnaire_contractuel` désigné.

| Test | Type de cas | Attendu |
|---|---|---|
| `test_commercial_gestion_requis_autorise_admin` | positif | admin passe |
| `test_commercial_gestion_requis_autorise_responsable` | positif | responsable_securite passe |
| `test_commercial_gestion_requis_refuse_directeur` | négatif | directeur (même gestionnaire du contrat) refusé — redirection vers dashboard |
| `test_commercial_gestion_requis_refuse_factotum` | négatif | refusé, redirection |
| `test_gestion_contrat_autorisee_admin` | positif | `True` pour admin, quel que soit le contrat |
| `test_gestion_contrat_autorisee_responsable` | positif | `True` pour responsable_securite |
| `test_gestion_contrat_autorisee_gestionnaire_du_contrat` | positif | `True` pour le directeur désigné `gestionnaire_contractuel` de ce contrat précis |
| `test_gestion_contrat_autorisee_directeur_non_gestionnaire` | négatif | `False` pour un directeur non désigné, même s'il a un `EtablissementUtilisateur` valide par ailleurs |
| `test_gestion_contrat_autorisee_factotum` | négatif | `False` |
| `test_verifier_acces_gestion_contrat_refus` | négatif | comportement exact dépend de la variante retenue au préalable — `assertRaises(Http404)` (variante A) ou `assertRedirects(..., reverse('registre:dashboard'))` (variante B) ; **à écrire seulement après arbitrage** |
| `test_demandes_avenant_visibles_admin_voit_tout` | positif | queryset contient les demandes de tous les établissements |
| `test_demandes_avenant_visibles_directeur_limite_a_son_perimetre` | négatif (partiel) | queryset exclut une demande portant sur un établissement hors périmètre |
| `test_demandes_avenant_visibles_gestionnaire_non_rattache_a_letablissement` | positif | un directeur désigné `gestionnaire_contractuel` du contrat voit les demandes même sur un établissement hors de son propre périmètre opérationnel (le pouvoir contractuel n'est pas borné par le périmètre opérationnel — point à confirmer, cf. §4 ci-dessous) |
| `test_gestionnaire_desactive_perd_lacces` (non-régression) | négatif | `contrat.gestionnaire_contractuel.is_active = False` → `gestion_contrat_autorisee` renvoie `False` (comportement Django standard déjà attendu, mais à couvrir explicitement) |

Suite complète (225 tests actuels + nouveaux) rejouée avant commit,
`manage.py check`, `makemigrations --check --dry-run` — même discipline
que les Lots précédents.

---

## 4. Cas positifs/négatifs de la matrice — couverture croisée

Reprise systématique de la matrice du document d'analyse (§4), pour
vérifier qu'aucune case n'est sans test prévu ci-dessus :

| Case de la matrice | Couverte par |
|---|---|
| admin — toutes actions | positif, tous les tests `*_admin*` |
| responsable_securite — toutes actions | positif, tous les tests `*_responsable*` |
| gestionnaire_contractuel — consultation/modification de **son** contrat | `test_gestion_contrat_autorisee_gestionnaire_du_contrat` |
| gestionnaire_contractuel — **pas** de droit sur un autre contrat que le sien | **manquant ci-dessus — à ajouter** : `test_gestion_contrat_autorisee_gestionnaire_dun_autre_contrat_refuse` (fixture : deuxième `ContratCommercial` avec un gestionnaire différent) |
| gestionnaire_contractuel — ne peut pas réassigner lui-même le gestionnaire (renouvellement) | `test_commercial_gestion_requis_refuse_directeur` (le gestionnaire est un directeur, donc déjà couvert — à condition que la fixture du test utilise bien le directeur désigné gestionnaire, pas un directeur quelconque) |
| directeur non gestionnaire — consultation limitée, pas de modification | `test_gestion_contrat_autorisee_directeur_non_gestionnaire` + `test_commercial_gestion_requis_refuse_directeur` |
| directeur — droit opérationnel inchangé (création établissement, soumission demande) | hors périmètre du Lot B, déjà couvert par les tests existants (`NouveauEtablissementTests`) — **non-régression à vérifier, pas de nouveau test** |
| factotum / prestataire — aucun accès | `test_commercial_gestion_requis_refuse_factotum`, `test_gestion_contrat_autorisee_factotum` |
| personne ne peut créer un `MouvementPerimetre` directement | déjà couvert au Lot A (`MouvementPerimetreModelTests` — contrainte au niveau modèle, pas une question de permission de vue) — **rappel, aucune action requise au Lot B** |

**Point relevé pendant cette couverture croisée, à trancher également** :
un `gestionnaire_contractuel` peut-il consulter/valider une demande
portant sur un établissement hors de son propre périmètre opérationnel
(`EtablissementUtilisateur`) ? L'architecture (§4.2) ne le précise pas
explicitement — elle sépare le pouvoir contractuel du périmètre
opérationnel, ce qui suggère que oui (le pouvoir contractuel porte sur
le contrat entier, pas établissement par établissement), mais ce n'est
pas écrit noir sur blanc. Proposé par défaut : **oui, le pouvoir
contractuel n'est pas borné par le périmètre opérationnel** — cohérent
avec la séparation stricte déjà actée (droit opérationnel ≠ pouvoir
contractuel). À confirmer avant développement.

---

## Résumé des points à trancher avant le GO Lot B

1. `verifier_acces_gestion_contrat` (et par extension
   `gestion_contrat_autorisee`) : refus par **redirection** ou par
   **Http404** ? (préalable, ci-dessus)
2. Un `gestionnaire_contractuel` a-t-il un pouvoir de consultation/
   validation qui dépasse son propre périmètre opérationnel
   d'établissements ? (§4, dernier point)

Aucun autre point ouvert identifié dans cette proposition — le reste
découle directement de la matrice déjà validée dans l'architecture
technique.
