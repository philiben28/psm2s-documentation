# Architecture — Phase 4, Lot 2 : lien direct vers la fiche depuis « Mes actions prioritaires »

Date : 05/07/2026
Statut : validé DT, en cours de développement.

---

## 1. Rappel de l'écart identifié

Backlog, Priorité 3 (« Widget "Mes prochaines actions" ») : *« Chaque ligne
doit ouvrir directement la fiche concernée. »*

Le bloc « Mes 5 actions prioritaires », livré en P4-L1 sur le tableau de
bord du Directeur, ne respecte pas cette exigence : chaque ligne pointe
vers `detail_etablissement` (la fiche générale de l'établissement) et non
vers la fiche du contrôle ou du contrat concerné. Le Directeur doit alors
chercher visuellement l'élément en retard parmi tous les contrôles de
l'établissement — exactement ce que la Vision interdit.

## 2. Principe d'architecture retenu (DT)

`collecter_conformite()` reste un moteur de calcul, agnostique de la
navigation. Il n'expose pas d'URL ; il expose la nature et l'identifiant
de la cible :

```python
{
    'cible_type': 'controle',   # ou 'contrat'
    'cible_pk': 42,
    ...
}
```

C'est la couche de présentation (le template) qui décide du lien à
construire selon `cible_type`. Cette séparation garde le moteur
réutilisable par un autre écran, une API ou une application mobile future,
sans qu'il ait à connaître les routes Django.

## 3. Modification exacte

- **`registre/tableau_bord.py`** : chaque entrée d'`alertes` gagne deux
  clés supplémentaires, `cible_type` et `cible_pk` :
  - alertes de type `retard`/`proche` (contrôles) → `cible_type='controle'`,
    `cible_pk=c.pk`.
  - alertes de type `contrat` → `cible_type='contrat'`,
    `cible_pk=contrat.pk`.
  - `etab_pk` reste présent (utilisé ailleurs / repli).
  - Aucun nouveau calcul, aucune nouvelle règle métier : les objets `c` et
    `contrat` sont déjà en main au moment de la construction de l'alerte,
    on ne fait qu'exposer leur `pk`.
- **`Templates/registre/dashboard.html`** : le lien de chaque ligne de
  « Mes 5 actions prioritaires » devient conditionnel :
  - `cible_type == 'controle'` → `{% url 'registre:modifier_controle' a.cible_pk %}`
  - `cible_type == 'contrat'` → `{% url 'registre:modifier_contrat' a.cible_pk %}`
  - sinon (repli) → `{% url 'registre:detail_etablissement' a.etab_pk %}`
- **`registre/views.py`** : aucune modification. `tableau_de_bord()`
  consomme déjà `collecter_conformite()['alertes']` ; les nouvelles clés
  sont ajoutées au dict existant sans effet sur son usage actuel (vérifié :
  la liste `alertes` n'est pas rendue comme liste de liens cliquables dans
  `tableau_de_bord.html` aujourd'hui — hors périmètre de ce lot, qui porte
  spécifiquement sur l'expérience Directeur).

## 4. Périmètre volontairement exclu

Le bloc « Échéances proches » (compteurs retard / aujourd'hui / cette
semaine) n'est pas concerné par ce lot : le backlog n'exige la navigation
directe que pour le widget « Mes prochaines actions » (Priorité 3). Les
compteurs restent des indicateurs agrégés, comme les 4 cartes
d'indicateurs clés.

## 5. Sécurité

`modifier_controle` et `modifier_contrat` appliquent déjà leur propre
contrôle de périmètre (vérifié dans le code existant). Le Directeur ne
peut de toute façon recevoir, dans ses alertes, que des contrôles/contrats
d'établissements de son périmètre (source : `etablissements`, déjà scopé
en amont dans `dashboard()`). Aucun risque IDOR introduit.

---

*Rédigé par le Lead Developer PSM2S, 05/07/2026.*
