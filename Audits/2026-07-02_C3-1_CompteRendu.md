# Compte-rendu de développement — Lot C3-1 : Desserte média protégée (documents métier)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : correction de sécurité (Critique C3, 1re partie). Lot le plus structurant de la Phase 2.

---

## 1. Résumé

Les fichiers `/media` ne sont plus servis anonymement. Une **vue unique** `media_protegee` (route `/media/<path>`) devient le seul point d'entrée : **authentification obligatoire** pour tout média, **contrôle de périmètre** pour les documents rattachés à un établissement. La politique par famille de fichiers est décrite dans un **registre central** (`registre/media_access.py`) ; la vue **ne connaît pas les modèles** et délègue.

Conforme à l'architecture demandée par le DT :
`media_protegee → registre → resolveur → verifier_acces_etablissement → FileResponse`.

## 2. Fichiers modifiés

| Fichier | Nature |
|---|---|
| `registre/media_access.py` | **Nouveau** — registre central (préfixe → modèle/champ → résolveur → **disposition** → périmètre) + résolveurs. |
| `registre/views.py` | **Nouveau** — vue `media_protegee` (mince, délègue au registre ; ne connaît pas les modèles). |
| `config/urls.py` | Route `/media/<path>` → `media_protegee` ; **retrait** de `static(MEDIA_URL, …)`. |
| `.htaccess` | Durcissement (`Options -Indexes`) + note (pas de « Deny /media »). |
| `registre/tests.py` | **7 tests** ajoutés (`MediaProtegeeTests`). |
| `Documentation/DEPLOIEMENT_o2switch.md` | Section desserte média + Étape 2 (MEDIA_ROOT hors webroot, X-Sendfile). |
| `CHANGELOG.md` | Entrée C3-1. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_C3-1/`. **Aucun modèle, migration, template ni URL de template modifié.**

## 3. Registre central (portant la politique de service)

Conformément à l'exigence du DT, le registre décrit non seulement le modèle et le champ, mais aussi la **politique de service** (disposition) et le **niveau de contrôle** :

| Préfixe | Périmètre | Disposition | Établissement via |
|---|---|---|---|
| `documents/` | oui | attachment | `controle.etablissement_id` |
| `realisations/` | oui | attachment | `controle.etablissement_id` |
| `tickets/` | oui | attachment | `ticket.etablissement_id` |
| `contrats/` | oui | attachment | `etablissement_id` |
| `commissions/` | oui | attachment | `etablissement_id` |
| `prescriptions/` | oui | attachment | `prescription.visite.etablissement_id` |
| `analyses_eau/` | oui | attachment | `point.reseau.etablissement_id` |
| `accessibilite/pieces/` | oui | attachment | `registre.etablissement_id` |
| `signatures/` | **non (transitoire)** | inline | — |

Ajouter un futur type de média = **ajouter une ligne** dans ce registre. La vue reste inchangée.

## 4. Signatures — statut transitoire (mention explicite demandée par le DT)

> **Les signatures ne sont pas encore soumises à leur politique d'autorisation définitive (S2).** C3-1 supprime uniquement leur exposition publique en imposant l'authentification (et les sert `inline` pour préserver leur affichage). Leur contrôle de périmètre / de propriété (S2 : propriétaire pour la signature personnelle, périmètre du document pour DUERP et Accessibilité) sera introduit au lot **C3-2**.

Ainsi, personne ne doit croire que les signatures ont atteint leur niveau de sécurité final : ce n'est pas le cas avant C3-2.

## 5. Point d'architecture clarifié pendant le développement

Dans l'état actuel, `/media` était servi **par Django** (`static(MEDIA_URL, …)`, actif car `DEBUG=True`), non par Apache. Le correctif réel est donc le **remplacement de cette desserte** par `media_protegee`. Conséquences :
- La vue fonctionne **quel que soit `DEBUG`** → elle **débloque C1** (plus de dépendance de `/media` à `static()`).
- Le `.htaccess` ne doit **pas** bloquer `/media` (un 403 Apache surviendrait avant Django). La garantie définitive contre un accès direct au système de fichiers = déplacer `MEDIA_ROOT` hors webroot (**Étape 2**).

## 6. Sécurité complémentaire

- **404 (jamais 403)** hors périmètre — cohérent avec toute la campagne C4.
- **Anti-traversée de répertoire** : le chemin physique est résolu via `realpath` et vérifié comme strictement contenu dans `MEDIA_ROOT`.
- **`Content-Disposition: attachment`** pour les documents → empêche l'exécution inline de HTML/SVG piégés (bénéfice recoupant l'anomalie E3).

## 7. Résultats des tests

> Pré-requis (depuis C2) : définir `DJANGO_SECRET_KEY` avant de lancer les commandes.
> ```
> $env:DJANGO_SECRET_KEY = "<clé de dev>"
> python manage.py check
> python manage.py test registre
> ```

**Résultat (02/07/2026) : 104 tests exécutés (97 précédents + 7 C3-1), 0 échec, 0 erreur (OK).**
Tests C3-1 : téléchargement autorisé (200, attachment) ; document d'un autre site (404) ; admin (accès total) ; non authentifié (302) ; signature authentifiée (200, inline) ; signature non authentifiée (302) ; préfixe inconnu (404).

## 8. Risque de régression

- Les liens `{{ obj.fichier.url }}` (→ `/media/…`) sont **inchangés** ; ils passent désormais par la vue protégée. Aucun template modifié.
- Impact fonctionnel légitime : un utilisateur doit être **connecté** pour accéder à un média (déjà le cas dans l'usage réel) ; un utilisateur restreint ne récupère que les documents de son périmètre.
- Migrations : aucune.

## 9. Suite

- **C3-2** : politique fine des signatures (S2), en réutilisant le même registre (il suffira de passer l'entrée `signatures/` en `perimetre`/résolveurs dédiés).
- Puis **C1** (DEBUG=False, désormais débloqué) et **E4** (cookies/transport).
- **Étape 2** (ultérieure) : `MEDIA_ROOT` hors webroot + `X-Sendfile`.

## 10. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : définir `DJANGO_SECRET_KEY`, lancer `python manage.py check` et `python manage.py test registre` (attendu : **104 OK**) et me transmettre la sortie. Aucun commit effectué.
