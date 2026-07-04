# Compte-rendu — Lot E5 : correction de la politique de visibilité DUERP

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : correction d'une incohérence de logique métier (droits). Anomalie unique. Referme l'incohérence résiduelle laissée volontairement après C4-5.

---

## 1. Anomalie traitée (E5)

Trois systèmes de droits coexistaient et se contredisaient sur le cas du **directeur** :
- `_get_etab_ids_autorises` (source de vérité) → directeur **restreint** à ses établissements ;
- `peut_tout_voir` (propriété de modèle) → directeur **« tout voir »**.

`duerp_liste` s'appuyait sur `peut_tout_voir` : un directeur voyait donc, dans la liste, les DUERP de **tous** les établissements (divulgation de métadonnées : établissement, année, statut, signataire). C'est l'incohérence **E5** de l'audit, et l'incohérence résiduelle que nous avions sciemment laissée après C4-5 (détail protégé, liste encore trop large).

## 2. Corrections

Deux modifications, constituant une seule anomalie (la politique de visibilité) :

1. **`registre/models.py` — `Utilisateur.peut_tout_voir`** : le directeur est retiré de la liste. La propriété renvoie désormais True uniquement pour `admin`, `responsable_securite` et superuser. Elle devient cohérente avec `_get_etab_ids_autorises`.

2. **`registre/views.py` — `duerp_liste`** : la vue ne s'appuie plus sur `peut_tout_voir`. Elle filtre par `_get_etab_ids_autorises(request.user)`, exactement comme `controles_global`, `tickets_global` et `interventions`. `None` → accès total (admin/responsable) ; ensemble d'IDs → liste restreinte.

Après ce lot, `peut_tout_voir` n'a plus aucun consommateur applicatif vivant (seule la méthode morte `peut_voir_etablissement` y fait encore référence). Sa correction élimine néanmoins un piège pour les développements futurs.

## 3. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/models.py` | `peut_tout_voir` : retrait du rôle `directeur` (+ docstring). |
| `registre/views.py` | `duerp_liste` : filtrage via `_get_etab_ids_autorises`. |
| `registre/tests.py` | **4 tests** ajoutés (`DuerpListeE5Tests`). |
| `CHANGELOG.md` | Entrée E5. |
| `Documentation/Audits/2026-07-02_E5_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_E5/extrait.py.bak`.

## 4. Périmètre respecté

- **Aucune modification** apportée aux vues objet DUERP (déjà traitées en C4-5).
- `peut_voir_etablissement` (models.py) **non réécrite** : méthode non appelée dans les vues ; sa dépendance à `peut_tout_voir` la rend simplement cohérente avec la nouvelle sémantique, sans effet fonctionnel. Un nettoyage éventuel relèverait d'un lot qualité distinct.
- Aucun modèle de base de données modifié, aucune migration, aucune URL touchée.

## 5. Résultats des tests

> **Exécutés et validés le 02/07/2026** (Python 3.13).

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 72 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........................................................................
----------------------------------------------------------------------
Ran 72 tests in 139.251s
OK
Destroying test database for alias 'default'...
```

**Résultat : 72 tests exécutés (68 précédents + 4 E5), 0 échec, 0 erreur (OK).**

Tests E5 (`DuerpListeE5Tests`) :
- `test_directeur_ne_voit_que_son_site` : la liste du directeur contient le DUERP du site A, **pas** celui du site B.
- `test_admin_voit_tous_les_duerp` / `test_responsable_voit_tous_les_duerp` : accès global conservé.
- `test_peut_tout_voir_semantique` : admin/responsable/superuser → True ; directeur/factotum/prestataire → False.

## 6. Analyse du risque de régression

- Surface : 2 zones (une propriété, une vue), plus les tests.
- `peut_tout_voir` : après E5, son seul consommateur applicatif (`duerp_liste`) ne l'utilise plus → sa correction ne peut casser aucun comportement vivant. Vérifié par grep : aucune utilisation en template, aucune autre vue.
- `duerp_liste` : la nouvelle logique est le motif déjà éprouvé dans trois autres vues liste. Admin/responsable conservent l'accès total ; directeur/factotum/prestataire sont restreints à leur périmètre — comportement attendu, couvert par les tests.
- Migrations : aucune.

## 7. État du chantier

L'incohérence E5 est refermée : la liste DUERP applique la même politique que le détail (C4-5) et que le reste de l'application. Restant : **Accessibilité**, **Bâtiments**, **mini-lot formulaires**.

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : lancer `python manage.py check` et `python manage.py test registre` (attendu : **72 OK**) et me transmettre la sortie. Aucun commit effectué.
