# Compte-rendu — Lot C2 : Externalisation et sécurisation de la `SECRET_KEY`

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : correction de sécurité (Critique C2 de l'audit). Première correction de la Phase 2, sur base INFRA-1.

---

## 1. Résumé

`SECRET_KEY` est désormais lue **exclusivement** depuis l'environnement, **sans valeur de secours**, avec échec explicite si absente. Les secrets en clair sont retirés du code. Décision DT : **Option 1 stricte partout**, aucun comportement spécial pour les tests. Conforme à l'Architecture de Production v1 (secure-by-default, une seule architecture, aucun comportement caché).

## 2. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `config/env.py` | **Ajout** `get_env_required(name)` : renvoie la variable ou lève `ImproperlyConfigured` (message explicite). |
| `config/settings.py` | `SECRET_KEY = get_env_required('DJANGO_SECRET_KEY')` — **fallback supprimé**. |
| `passenger_wsgi.py` | Retrait du `os.environ['DJANGO_SECRET_KEY'] = '…'` en clair. |
| `passenger_wsgi_formation.py` | Idem. |
| `registre/tests.py` | **3 tests** ajoutés (`get_env_required` : présent / absent / vide). |
| `Documentation/DEPLOIEMENT_o2switch.md` | Section C2 : variable requise, génération, **procédure de rotation**, invalidation des sessions. |
| `CHANGELOG.md` | Entrée C2. |

Sauvegarde (avec secrets originaux, hors dépôt) : `Sauvegardes/2026-07-02_avant_C2/extrait.py.bak`.

## 3. Comportement

- **Tous environnements** : `DJANGO_SECRET_KEY` absente/vide → `ImproperlyConfigured: DJANGO_SECRET_KEY environment variable is required.` L'application refuse de démarrer. Aucune exception pour les tests (décision DT).
- **Aucun secret** ne subsiste dans le code (`settings.py`, `passenger_wsgi*.py`). Le fallback `django-insecure-…` est supprimé.
- **Identité dev / préprod / prod** : le code est strictement le même partout ; seule la variable d'environnement change. Propriété recherchée par le DT.

## 4. Rotation (responsabilité exploitant — DT)

Les clés historiques sont **compromises** (présentes dans le code et l'historique). La procédure de rotation est documentée (`DEPLOIEMENT_o2switch.md` §3 bis) et reste sous la responsabilité du DT :
génération → sauvegarde → création variable cPanel (prod + formation, clés distinctes) → vérification → déploiement C2 → redémarrage Passenger → contrôle.
**Ordre impératif** : la variable doit exister dans cPanel **avant** le déploiement de C2. **Conséquence** : rotation = invalidation des sessions actives et des liens de réinitialisation en cours.

## 5. Résultats des tests

> **Important — pré-requis d'exécution (nouveau) :** depuis C2, les settings ne se chargent plus sans `DJANGO_SECRET_KEY`. Avant de lancer `check` / `test`, définir la variable :
> ```
> $env:DJANGO_SECRET_KEY = "<clé de dev quelconque>"
> python manage.py check
> python manage.py test registre
> ```

**Résultat (02/07/2026, `DJANGO_SECRET_KEY` posée en local) :**
```
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py test registre
Found 97 test(s).
...
Ran 97 tests in 163.127s
OK
```
**97 tests exécutés (94 précédents + 3 C2), 0 échec, 0 erreur (OK).**
Les 3 nouveaux tests valident `get_env_required` (présent → valeur ; absent → `ImproperlyConfigured` ; vide → `ImproperlyConfigured`).

## 6. Analyse du risque de régression

- **Code** : faible. Une ligne de settings, un helper, deux `passenger_wsgi` nettoyés.
- **Workflow** : changement assumé et validé — la variable `DJANGO_SECRET_KEY` doit être définie pour lancer toute commande Django (dev comme prod). Documenté.
- **Production** : le déploiement de C2 **exige** la variable cPanel au préalable (sinon non-démarrage — comportement voulu). Coordonné par la procédure de rotation.
- Migrations : aucune.

## 7. Conformité à l'Architecture de Production v1

- §4.1 (secrets par environnement, défaut sûr) : **conforme**. Un secret absent ne donne jamais une valeur faible : il **bloque**.
- Aucun comportement caché ni exception de test (décision DT). Une seule architecture, identique partout.

## 8. Suite

Prochain lot du séquencement : **C3 — Protection des médias et préparation de la desserte** (débloque ensuite C1). C3 réutilisera la primitive de périmètre de la campagne C4.

## 9. Disponibilité pour revue

Développement et documentation terminés. Avant validation/commit : définir `DJANGO_SECRET_KEY` en local, puis lancer `python manage.py check` et `python manage.py test registre` (attendu : **97 OK**) et me transmettre la sortie. Aucun commit effectué.
