# Compte-rendu de développement — Lot C3-2 : Politique d'autorisation des signatures (S2)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 03/07/2026
Nature : correction de sécurité (Critique C3, 2e partie). **Clôture du chantier média.**

---

## 1. Résumé

Fin du régime transitoire de C3-1 : les signatures reçoivent leur **politique définitive S2**, et le registre média devient **totalement générique**. Chaque règle porte une primitive d'autorisation `autoriser(user, chemin) -> bool`, construite par des **fabriques** ; la vue `media_protegee` ne fait plus que : trouver la règle → `autoriser()` → servir.

Politiques de signature :
- **Personnelle** (`signatures/`) → **propriétaire strict** (aucune exception, même admin/superuser).
- **DUERP** (`signatures/duerp/`) → **périmètre** de l'établissement du DUERP.
- **Accessibilité** (`signatures/accessibilite/`) → **périmètre** de l'établissement du registre.

## 2. Fichiers modifiés

| Fichier | Nature |
|---|---|
| `registre/media_access.py` | `RegleMedia` généralisée (`autoriser`) ; fabriques `par_perimetre` / `par_proprietaire` ; résolveurs signatures DUERP & accessibilité ; réordonnancement (préfixes spécifiques d'abord). |
| `registre/views.py` | `media_protegee` **simplifiée** : une seule délégation `regle.autoriser(...)`, plus aucune branche conditionnelle. |
| `registre/tests.py` | 1 test C3-1 adapté + **7 tests** S2 (`SignatureAccessTests`). |
| `CHANGELOG.md`, `DEPLOIEMENT_o2switch.md` | Signatures au niveau définitif. |

Sauvegarde : `Sauvegardes/2026-07-03_avant_C3-2/`. **Aucun modèle, migration, template ni URL de template.**

## 3. Architecture (conforme aux décisions DT)

Le registre ne connaît plus qu'**une** notion : la **politique d'autorisation**. « Périmètre » et « propriétaire » n'existent plus comme champs — ce sont des **fabriques** d'autoriseurs :

```
RegleMedia(prefixe, disposition, autoriser, libelle)

autoriser = par_perimetre(resolveur)   # documents + signatures de documents
autoriser = par_proprietaire()         # signature personnelle
# extensible : par_role(...), par_token(...)  → sans toucher la vue ni la structure
```

La vue est agnostique :
```
regle = regle_pour_chemin(chemin)      # préfixe inconnu -> 404 (sans exception)
if not regle.autoriser(user, chemin):  # non autorisé -> 404 (jamais 403)
    404
FileResponse(...) + Content-Disposition (disposition de la règle)
```

`media_access.py` devient ainsi le composant central de sécurité des médias, pendant de `verifier_acces_etablissement` pour les objets métier.

## 4. Décisions appliquées

- ✅ Primitive unique `autoriser(user, chemin)` ; vue totalement agnostique.
- ✅ Signature personnelle = **propriétaire strict** (même admin refusé). Conséquence assumée : l'aperçu d'une signature d'autrui dans l'admin Django affichera une image cassée — limitation acceptée au profit de la confidentialité.
- ✅ Signatures DUERP / Accessibilité = périmètre.
- ✅ Un seul lot.
- ✅ Tout préfixe absent du registre → 404.

## 5. Résultats des tests

> Pré-requis : `DJANGO_SECRET_KEY` définie en local.
> ```
> $env:DJANGO_SECRET_KEY = "<clé de dev>"
> python manage.py check
> python manage.py test registre
> ```

**Résultat (03/07/2026) : 111 tests exécutés (104 précédents + 7 C3-2), 0 échec, 0 erreur (OK).** Commit `fc8fcbb`.
Tests S2 : propriétaire OK (inline) ; autre utilisateur / admin / superuser refusés (404) ; signature DUERP et Accessibilité soumises au périmètre (200 site autorisé / 404 autre) ; admin accède aux signatures **de documents** (périmètre total). Le test C3-1 de signature transitoire a été adapté (une signature sans propriétaire → 404).

## 6. Risque de régression

- Documents métier (C3-1) : comportement **inchangé** (ils passent désormais par `par_perimetre`, strictement équivalent à l'ancien contrôle de périmètre).
- Signatures : passage de « authentifié » à S2 — changement **voulu**, couvert par les tests.
- Migrations : aucune.

## 7. Bilan du chantier média

Terminé. Plus aucun média servi anonymement ; documents et signatures soumis à une politique d'autorisation centralisée et extensible. Reste (hors chantier média) : **C1** (DEBUG=False, mise en service), **E4** (cookies/transport), et l'**Étape 2** (MEDIA_ROOT hors webroot + X-Sendfile).

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : définir `DJANGO_SECRET_KEY`, lancer `check` et `test registre` (attendu : **111 OK**) et me transmettre la sortie. Aucun commit effectué.
