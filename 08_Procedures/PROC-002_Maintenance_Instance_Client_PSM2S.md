# PROC-002 — Maintenance d'une instance PSM2S déployée

Statut : document permanent et officiel de la plateforme (Lot L3.3,
04/07/2026), au même titre que `PROC-001` et `DEPLOIEMENT_o2switch.md`.

## Périmètre actuel — note importante

À ce jour, PSM2S n'a pas encore d'architecture Core + Variantes (L3.4,
non ouvert) : chaque environnement déployé (formation, production, et
demain une éventuelle instance cliente) exécute l'intégralité du même
code. Le terme « instance » désigne donc ici **un environnement déployé
dans son ensemble**, pas une variante cliente distincte avec sa propre
configuration. **Cette procédure devra être complétée après L3.4** pour
distinguer un correctif touchant le Core (impacte toutes les instances)
d'un correctif touchant une seule variante.

Cette procédure complète `PROC-001` (déploiement) sans le dupliquer : elle
s'applique quand le besoin n'est **pas** de déployer un lot déjà validé
et testé en développement, mais de **corriger un défaut constaté sur une
instance déjà en ligne**.

---

## Étape 1 — Identifier précisément l'instance et le défaut

- Quel environnement est concerné (formation, production, autre) ?
- Quel est le symptôme exact (message d'erreur, comportement observé,
  URL, rôle utilisateur concerné) ?
- Le défaut est-il reproductible en développement local, ou seulement sur
  l'instance ?

Ne pas corriger avant d'avoir répondu à ces trois questions — cf. principe
« un objectif = un lot » de la Méthodologie PSM2S, qui s'applique aussi
aux correctifs.

## Étape 2 — Vérifier l'état réel de l'instance avant de corriger

**Leçon directe de L3.1** : ne jamais supposer que le code en ligne sur
une instance correspond exactement au dépôt Git (`HEAD` ou un commit
donné), tant que cette instance n'est pas déployée exclusivement via Git.

- Si le fichier suspecté est identifiable, comparer son contenu réel sur
  le serveur (cPanel Gestionnaire de fichiers, ou terminal) avec la
  version du dépôt, avant toute hypothèse sur la cause.
- En cas de doute sur l'ampleur de la divergence, ne pas se fier à un
  `git diff` ciblé (voir `PROC-001` Étape 2) — vérifier directement sur
  le serveur.

## Étape 3 — Corriger en local (développement)

- Reproduire le défaut en local si possible, avant d'écrire le correctif.
- Périmètre du correctif strictement limité au défaut identifié :
  **aucun refactoring non demandé, aucune modification hors périmètre**
  (Méthodologie PSM2S, principes de gouvernance).
- Documenter le correctif proportionnellement à son importance (principe
  de proportionnalité, `IA_RULES` §Principe de proportionnalité) : une
  correction mineure ne demande pas un compte-rendu de lot complet, mais
  mérite au minimum une ligne dans le commit Git et, si elle touche une
  décision déjà consignée, une mise à jour de `DECISIONS.md`.

## Étape 4 — Tester

- Tests automatisés existants (`python manage.py test registre`) —
  aucune régression.
- Test manuel ciblé sur le défaut corrigé, en conditions aussi proches que
  possible de l'instance concernée (rôle utilisateur, données).

## Étape 5 — Déployer le correctif sur l'instance concernée

Le correctif est ciblé et son contenu est connu avec certitude (contrairement
à une resynchronisation complète où l'état de départ est incertain) : un
transfert du ou des fichiers modifiés suffit, **à condition** d'avoir
vérifié l'Étape 0 de `PROC-001` (fichiers spécifiques au serveur) si le
correctif touche l'un d'eux.

- Sauvegarde du ou des fichiers concernés avant écrasement (`PROC-001`
  Étape 1, à l'échelle du correctif).
- Transfert du ou des fichiers corrigés vers l'instance concernée
  **uniquement** — ne pas propager à d'autres instances tant que le
  correctif n'y a pas été validé séparément, sauf si le défaut les
  concerne toutes et que c'est une décision explicite.
- Si le correctif touche des dépendances (migration, variable
  d'environnement) : dérouler les étapes correspondantes de `PROC-001`
  (collectstatic / migrate / check --deploy / redémarrage Passenger).
- **Vérifier `DJANGO_SETTINGS_MODULE`** (voir `PROC-001` Étape 4) avant
  toute commande `migrate` : sur une instance dont `passenger_wsgi.py` fixe
  un settings dédié, préfixer explicitement la commande
  (`DJANGO_SETTINGS_MODULE=... python manage.py migrate`), sous peine de
  migrer silencieusement une base différente de celle réellement servie.
  Confirmer ensuite avec `showmigrations`, sous le même module.

## Étape 6 — Vérifier sur l'instance

- Le défaut initial a disparu.
- Aucune régression visible sur les écrans adjacents.
- `check --deploy` toujours vert (si le correctif touche la configuration).

## Étape 7 — Traçabilité

**Principe** : aucune modification de code n'est considérée comme
terminée tant qu'elle n'est pas commitée dans le dépôt Git. Le dépôt Git
constitue l'unique source de vérité du projet. Ce principe s'applique
sans exception : développement local, correctif de production, correctif
de formation, ou future maintenance d'une variante cliente — même quand
l'instance corrigée n'est elle-même pas suivie par Git, elle ne doit
jamais diverger durablement de ce qui est committé.

- Note courte dans `DECISIONS.md` si le correctif révèle ou modifie une
  décision déjà consignée.
- Mention dans un futur journal des livraisons (L3.6, non ouvert) : quelle
  instance, quelle date, quel correctif, quel commit.

---

## Modèle de référence — migration progressive d'un champ existant

Retenu comme méthode standard (DT, 05/07/2026) pour toute évolution de
schéma touchant des données déjà en place, à partir de l'expérience réelle
de **P4-L3 — Référentiel Prestataires** (`DECISIONS.md`) :

1. **Créer la nouvelle entité/le nouveau champ**, en coexistence avec
   l'ancien (nullable, aucune rupture de l'existant).
2. **Migration de données** : peupler le nouveau champ à partir de
   l'ancien (dédoublonnage minimal si la donnée source est en texte
   libre), de façon idempotente.
3. **Validation technique** : tests automatisés, migration exécutée sans
   erreur en développement, vérification qu'aucune donnée n'est restée
   orpheline.
4. **Validation sur une instance déjà déployée** (formation avant
   production) : mêmes vérifications, en conditions réelles — c'est ce qui
   a révélé, lors de P4-L3, un décalage `DJANGO_SETTINGS_MODULE` resté
   invisible jusque-là (cf. `PROC-001` Étape 4).
5. **Suppression de l'ancien champ**, seulement une fois les 4 étapes
   précédentes validées, dans un lot au périmètre strictement délimité
   (suppression + adaptation des consommateurs déjà identifiés +
   adaptation des tests — rien de plus).

Cette séquence réduit le risque à chaque étape sans imposer de délai
artificiel : le passage d'une étape à la suivante est conditionné à une
validation technique, jamais à une durée d'attente.

---

## Historique

- **v1.0** (04/07/2026, L3.3) : première version. Périmètre volontairement
  limité à la réalité actuelle (une instance = un environnement complet) ;
  à réviser après L3.4 (architecture Core + Variantes) pour distinguer
  correctif Core / correctif Variante.
