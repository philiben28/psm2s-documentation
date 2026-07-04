# Compte-rendu de développement — Lot C4-1 : correction IDOR (module Établissement)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Protocole : PSM2S — étapes 5 (développement), 6 (tests), 7 (documentation). En attente des étapes 8-10 (revue DT, validation, commit).

---

## 1. Résumé des développements réalisés

Correction de la faille IDOR (anomalie C4) **sur le seul module Établissement**, conformément au périmètre du lot. Un contrôle d'accès au niveau de l'objet a été ajouté : un utilisateur restreint ne peut plus atteindre un établissement hors de son périmètre en manipulant l'identifiant d'URL.

Le travail se décompose en :
1. Ajout d'un **helper générique et centralisé** dans `registre/permissions.py`, réutilisable par tous les modules actuels et futurs.
2. Sécurisation des **3 vues Établissement** (`detail_etablissement`, `modifier_etablissement`, `archiver_etablissement`).
3. Écriture d'une **suite de tests d'accès** (`registre/tests.py`, jusqu'ici vide).
4. Mise à jour de la **documentation** et du **CHANGELOG**.

Aucun modèle, migration, URL ou logique métier n'a été modifié. Aucun refactoring. Aucun autre module n'a été touché.

## 2. Liste complète des fichiers modifiés

| Fichier | Type de modification |
|---|---|
| `registre/permissions.py` | **Ajout** de 4 fonctions (bloc « CONTRÔLE D'ACCÈS AU NIVEAU DE L'OBJET ») + 2 imports (`get_object_or_404`, `Http404`). Aucune modification des décorateurs existants. |
| `registre/views.py` | **Import** du helper ; **3 vues** modifiées (1 à 2 lignes chacune) : remplacement du `get_object_or_404(Etablissement, …)` par `get_etablissement_ou_404(request.user, …)`. |
| `registre/tests.py` | **Création** de la suite de tests d'accès Établissement. |
| `CHANGELOG.md` | **Création** + entrée C4-1. |
| `Documentation/Audits/2026-07-02_C4-1_CompteRendu.md` | Ce document. |

Sauvegardes préalables : `Sauvegardes/2026-07-02_avant_C4-1_IDOR/` (`permissions.py.bak`, `views_etablissement_extrait.py.bak`).

## 3. Justification technique des choix

- **Centralisation dans `permissions.py`** (décision DT) : toute la logique d'autorisation vit désormais au même endroit que les décorateurs de rôle. Le module expose une primitive générique `verifier_acces_etablissement(user, etablissement_id)` que les futurs lots réutiliseront (chaque module récupérera l'ID d'établissement de son objet puis appellera cette primitive).
- **`_get_etab_ids_autorises` comme source unique de vérité** (décision DT) : le helper l'appelle exclusivement. Aucune règle de périmètre n'est réécrite ; les listes (déjà sûres) et les nouvelles vues détail partagent donc exactement la même définition de périmètre.
- **HTTP 404 en cas de refus** (décision DT) : `verifier_acces_etablissement` lève `Http404` et non `PermissionDenied` (403), pour ne pas révéler l'existence de l'objet.
- **Import différé de `_get_etab_ids_autorises`** : ce helper réside dans `views.py`, lequel importe déjà `permissions.py`. Un import au niveau module créerait une **dépendance circulaire**. L'import est donc réalisé dans le corps des fonctions (au moment de la requête, quand `views.py` est entièrement chargé). Choix retenu plutôt que de déplacer `_get_etab_ids_autorises` (qui aurait constitué un refactoring hors périmètre, touchant de nombreuses vues).
- **Paramètre `actif`** : `get_etablissement_ou_404(..., actif=True)` par défaut (détail/modification n'opèrent que sur des sites actifs, comportement d'origine) ; `actif=False` pour l'archivage, qui doit cibler un site actif pour le désactiver (comportement d'origine conservé).
- **Conservation du comportement fonctionnel** : les utilisateurs légitimes gardent exactement leurs accès. Seul changement de comportement assumé : un prestataire hors périmètre recevait auparavant une **redirection** vers le dashboard sur `detail_etablissement` ; il reçoit désormais un **404**, conformément à l'architecture validée (et le contrôle couvre maintenant aussi directeur et factotum, jusque-là non vérifiés).

## 4. Résultats des tests

> **Exécutés et validés le 02/07/2026** dans l'environnement PSM2S du poste de développement (Python 3.13, `python manage.py`). Le bac à sable Linux de la session étant indisponible, l'exécution a été faite manuellement par le Product Owner / Lead Developer.

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 17 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................
----------------------------------------------------------------------
Ran 17 tests in 32.393s
OK
Destroying test database for alias 'default'...
```

**Résultat : 17 tests exécutés, 0 échec, 0 erreur (OK). `check` sans anomalie.**
L'import différé du helper est validé de fait (aucun import circulaire au démarrage).

Détail des tests (`registre/tests.py`) et résultat **constaté (tous OK)** :

| Classe / test | Attendu |
|---|---|
| `HelperPerimetreTests.test_acces_total_pour_admin_et_responsable` | `etablissements_autorises` renvoie `None` pour admin/responsable/superuser |
| `…test_directeur_perimetre_restreint` | site A dans le périmètre, site B non |
| `…test_acces_etablissement_autorise` | directeur : True sur A, False sur B ; admin : True partout |
| `…test_get_etablissement_ou_404_leve_404_hors_perimetre` | objet renvoyé sur A, `Http404` sur B |
| `…test_factotum_via_ticket` | factotum : True sur A (ticket), False sur B |
| `…test_prestataire_sans_ticket_naccede_a_rien` | False partout |
| `DetailEtablissementTests.test_directeur_accede_a_son_etablissement` | 200 |
| `…test_directeur_refuse_autre_etablissement_404` | 404 |
| `…test_admin_accede_a_tous_les_etablissements` | 200 / 200 |
| `…test_responsable_accede_a_tous` | 200 |
| `…test_factotum_accede_via_ticket_mais_pas_ailleurs` | 200 (A) / 404 (B) |
| `…test_prestataire_sans_ticket_refuse_404` | 404 |
| `ModifierEtablissementTests` (3 tests) | directeur : 200 sur A, 404 sur B ; admin : 200 |
| `ArchiverEtablissementTests` (2 tests) | admin : 200 ; directeur : 302 (bloqué au niveau du rôle par `@admin_requis`) |

Vérifications statiques réalisables (lecture de code) : cohérence des noms de vues avec `urls.py` ✓, absence de nouvel import circulaire au niveau module ✓ (import différé), `get_object_or_404`/`redirect`/`TicketTravaux` restent utilisés ailleurs et donc toujours importés ✓.

## 5. Analyse du risque de régression

- **Surface** : très réduite — 3 vues, modifications de 1 à 2 lignes chacune, plus un ajout de fonctions isolées (aucune fonction existante modifiée dans `permissions.py`).
- **Risque de sur-restriction** : le helper délègue à `_get_etab_ids_autorises`, déjà utilisé et éprouvé dans les listes ; le périmètre calculé est donc identique à celui déjà appliqué ailleurs → risque faible qu'un utilisateur légitime perde l'accès. Les tests par rôle couvrent explicitement ce point.
- **Changement de comportement connu** : prestataire hors périmètre sur `detail_etablissement` → 404 au lieu d'une redirection. Intentionnel et validé. À signaler aux utilisateurs si un message d'erreur convivial est souhaité (amélioration UX possible, hors périmètre).
- **Import circulaire** : neutralisé par l'import différé ; à confirmer par le démarrage de l'application (`manage.py check`) dans votre environnement.
- **Impact Lot 1 (Calendrier)** : nul — la vue `calendrier` n'est pas touchée et filtre déjà correctement.
- **Migrations** : aucune (confirmé, aucun changement de modèle).

## 6. Documentation mise à jour

- `CHANGELOG.md` (créé) — entrée C4-1.
- Ce compte-rendu (`Documentation/Audits/2026-07-02_C4-1_CompteRendu.md`).
- Docstrings détaillées dans `registre/permissions.py` (fonctionnement, décisions DT, note anti-cycle) et commentaires « Lot C4-1 » dans les vues modifiées.

## 7. Recommandations pour le Lot C4-2

- **Cible proposée : module Contrôles** (`modifier_controle`, `nouveau_controle`, `nouvelle_realisation`, `historique_controle`) — cœur métier, forte valeur de sécurisation. Motif : récupérer l'objet, puis `verifier_acces_etablissement(request.user, controle.etablissement_id)`.
- Réutiliser **exclusivement** la primitive `verifier_acces_etablissement` (ne pas recréer de logique).
- Envisager une variante d'aide `get_objet_ou_404(model, pk, user, chemin_etablissement)` si la répétition le justifie sur les objets enfants — à valider par le DT au lot suivant.
- Traiter séparément le **module Bâtiments** (`nouveau_batiment`, `modifier_batiment`, `supprimer_batiment`) : volontairement laissé hors C4-1 car modèle distinct (`Batiment`).
- Corriger l'incohérence **E5** (`peut_tout_voir` accorde « tout » au directeur) lors du lot DUERP, car elle interfère avec `duerp_liste`.
- Prévoir le **filtrage des `queryset`** de formulaires (ex. `InterventionForm`) dans le lot du module concerné.
- **Prérequis** : disposer d'un environnement d'exécution pour lancer la suite de tests à chaque lot (le bac à sable de session ne peut pas l'assurer).

## 8. Confirmation de disponibilité pour revue

Le développement du Lot C4-1 est **terminé côté code et documentation** et prêt pour votre revue technique (étape 8). 

Réserve explicite : la suite de tests **n'a pas pu être exécutée** dans cet environnement (VM indisponible). Je recommande, avant la validation finale (étape 9) et le commit documenté (étape 10), de lancer dans le staging PSM2S :
```
python manage.py check
python manage.py test registre
```
et de me transmettre la sortie si un ajustement s'avérait nécessaire.
