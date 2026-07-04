# Compte-rendu — Lot BUG-TPL-01 : correction du template `modifier_batiment.html`

Destinataire : Directeur Technique
Rédacteur : Lead Developer PSM2S
Date : 02/07/2026
Nature : correction de bug (template). Dépendance explicite de C4-7.

---

## 1. Anomalie

`Templates/registre/modifier_batiment.html`, ligne 1 : le template étendait
`{% extends "registre/base.html" %}`. Or le template de base du projet est
`base.html` (racine de `Templates/`) ; `registre/base.html` n'existe pas.
Conséquence : `TemplateDoesNotExist` → HTTP 500 à tout affichage (GET) de la
page « Modifier bâtiment ».

## 2. Découverte

Révélée par les tests du lot **C4-7** (`test_modifier_batiment`,
`test_admin_modifie_partout`), premiers à exercer le rendu GET de cette vue.
Bug **pré-existant**, indépendant du contrôle d'accès C4-7 (les cas 404 hors
périmètre passaient ; seuls les accès autorisés atteignaient le rendu cassé).

## 3. Correction

Une ligne, périmètre validé en revue :
```
- {% extends "registre/base.html" %}
+ {% extends "base.html" %}
```
Aucun autre changement.

## 4. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `Templates/registre/modifier_batiment.html` | ligne 1 : `{% extends %}` corrigé. |
| `CHANGELOG.md` | Entrée BUG-TPL-01. |
| `Documentation/Audits/2026-07-02_Anomalies_Restantes.md` | BUG-TPL-01 en « Résolues ». |
| `Documentation/Audits/2026-07-02_BUG-TPL-01_CompteRendu.md` | Ce document. |

Sauvegarde : `Sauvegardes/2026-07-02_avant_BUG-TPL-01/`.

## 5. Tests

Aucun test ajouté : la correction est validée par le passage au vert des tests
C4-7 qui échouaient (`test_modifier_batiment`, `test_admin_modifie_partout`).

Résultat (02/07/2026) : `python manage.py test registre` → **85 tests OK** (0 échec).
Les deux tests bâtiment qui échouaient avant BUG-TPL-01 passent désormais.

## 6. Risque de régression

Nul. Le template s'aligne sur la convention de tous les autres templates du
projet (`{% extends "base.html" %}`).

## 7. Observation hors périmètre (non corrigée)

Le même template comporte un `<form>` imbriqué dans un autre `<form>`
(lignes ~14 et ~57), ce qui est du HTML invalide. **Non touché** (hors périmètre
de BUG-TPL-01). À qualifier en revue si le DT souhaite l'inscrire au registre.

## 8. Chronologie

```
C4-7 (dev)  →  BUG-TPL-01 (fix template)  →  85 tests verts  →  validation BUG-TPL-01  →  commit BUG-TPL-01  →  validation C4-7  →  commit C4-7
```
