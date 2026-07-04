# Compte-rendu de développement — Lot C4-5 : correction IDOR (module DUERP)

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Protocole PSM2S : étapes 5 (dev), 6 (tests), 7 (doc). En attente 8-10.

---

## 1. Résumé

Sécurisation IDOR des **vues objet du module DUERP**, objectif unique du lot. Conformément à la décision du DT (deux lots distincts), ce lot **ne touche ni `duerp_liste` ni la propriété `peut_tout_voir`** : ces deux éléments constituent l'anomalie **E5** (logique métier de visibilité) et seront traités dans un lot dédié. Aucune modification de modèle, migration, URL ou logique métier ; aucune fonction ajoutée à `permissions.py`.

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `registre/views.py` | **11 vues** DUERP sécurisées (1 à 2 lignes chacune). |
| `registre/tests.py` | **11 tests** ajoutés (`DuerpAccesTests` + base `BaseAccesDUERP`). |
| `CHANGELOG.md` | Entrée C4-5. |
| `Documentation/Audits/2026-07-02_C4-5_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_C4-5_IDOR/`.

## 3. Vues sécurisées et chemins de remontée

| Vue | Contrôle d'objet |
|---|---|
| `duerp_nouveau(etab_pk)` | `get_etablissement_ou_404(user, etab_pk, actif=False)` |
| `duerp_detail(pk)` | `verifier_acces_etablissement(user, duerp.etablissement_id)` |
| `duerp_checklist(unite_pk)` | `… unite.duerp.etablissement_id` |
| `duerp_plan_action(pk)` | `… duerp.etablissement_id` |
| `duerp_action_creer(duerp_pk)` | `… duerp.etablissement_id` |
| `duerp_action_modifier(pk)` | `… action.duerp.etablissement_id` |
| `duerp_creer_ticket(action_pk)` | `… action.duerp.etablissement_id` |
| `duerp_modifier(pk)` | `… duerp.etablissement_id` |
| `duerp_imprimer(pk)` | `… duerp.etablissement_id` |
| `duerp_signer(pk)` | `… duerp.etablissement_id` (vérifié **avant** la logique de signature) |
| `duerp_supprimer_signature(pk)` | `… duerp.etablissement_id` |

Notes :
- `duerp_nouveau` : `actif=False` pour **conserver exactement** le comportement d'origine (l'appel initial ne filtrait pas sur `actif`).
- `duerp_signer` conserve sa vérification `DroitSignature.peut_signer` ; le contrôle de périmètre s'ajoute **avant**, sans la remplacer (défense complémentaire, pas de doublon).
- `duerp_supprimer_signature` : la ligne dupliquée `user = request.user` (anomalie F2) a été **volontairement conservée** pour garder ce lot strictement additif ; son nettoyage relèvera d'un lot de qualité distinct.

## 4. Résultats des tests

> **Exécutés et validés le 02/07/2026** (Python 3.13), après la correction du lot **M11** dont C4-5 dépend (voir compte-rendu M11).

Sortie réelle :
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 68 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
....................................................................
----------------------------------------------------------------------
Ran 68 tests in 134.518s
OK
Destroying test database for alias 'default'...
```

**Résultat : 68 tests exécutés (57 précédents + 11 C4-5), 0 échec, 0 erreur (OK).**
Le premier passage avait révélé le bug latent M11 (`test_detail`) ; après correction de M11, la suite est intégralement verte.

Chaque test compare, pour un directeur rattaché au site A : accès à l'objet du site A vs objet du site B. Codes attendus : **200 / 404** pour les vues de rendu ; **302 / 404** pour les trois vues à effet (`duerp_creer_ticket`, `duerp_signer`, `duerp_supprimer_signature`), où l'accès autorisé produit une redirection et l'accès hors périmètre un 404.

## 5. Analyse du risque de régression

- Surface : 11 vues, 1-2 lignes chacune, aucune fonction existante altérée.
- Périmètre = source unique de vérité (`_get_etab_ids_autorises`).
- **Incohérence résiduelle assumée et documentée** (validée par le DT) : tant que le lot E5 n'est pas fait, `duerp_liste` continue d'afficher au directeur les DUERP d'autres établissements ; un clic mènera désormais à un **404** (détail protégé par ce lot). Ce n'est pas un trou d'accès sur le détail, mais une divulgation de métadonnées sur la liste + une UX incohérente temporaire. Recommandation : enchaîner E5 rapidement.
- Migrations : aucune.

## 6. Note sur la frontière C4-5 / E5

- **C4-5 (ce lot)** : contrôle d'accès aux **objets** DUERP (vues détail/édition/action/signature). Mécanisme : `verifier_acces_etablissement` → `_get_etab_ids_autorises`.
- **E5 (lot suivant)** : la vue **liste** `duerp_liste` et la propriété `peut_tout_voir` (models.py l.78), unique consommateur vivant étant `duerp_liste` (views.py l.2080). `peut_voir_etablissement` (models.py l.82) est définie mais non appelée dans les vues — à nettoyer/aligner dans E5.

## 7. Recommandations pour la suite

- **E5** : aligner `peut_tout_voir` / `peut_voir_etablissement` sur `_get_etab_ids_autorises` et faire filtrer `duerp_liste` par le même périmètre. Anomalie unique, lot court.
- Puis **Accessibilité**, **Bâtiments**, et le **mini-lot formulaires**.

## 8. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : lancer `python manage.py check` et `python manage.py test registre` (attendu : 68 OK) et me transmettre la sortie. Aucun commit effectué.
