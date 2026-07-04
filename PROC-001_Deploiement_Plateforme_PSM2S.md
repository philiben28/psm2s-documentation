# PROC-001 — Déploiement d'une plateforme PSM2S

Statut : document permanent et officiel de la plateforme (Lot L3.2,
04/07/2026), au même titre que `DEPLOIEMENT_o2switch.md`.
Rédigé à partir de l'expérience réelle du déploiement L3.1
(resynchronisation de la plateforme formation), pas d'une procédure
théorique — voir `Documentation/Developpements/2026-07-04_L3.1_Resynchronisation_Formation_CompteRendu.md`
pour le détail des incidents ayant produit cette procédure.

## Champ d'application

Cette procédure s'applique à **tout déploiement** d'une plateforme PSM2S :
mise à jour d'un environnement existant (formation, production) ou mise
en place d'un nouveau serveur (future instance cliente). Elle décrit le
**mécanisme** de déploiement. Le détail des variables de sécurité
(`DJANGO_SECRET_KEY`, `DJANGO_SSL`, HSTS…) reste dans
`Documentation/DEPLOIEMENT_o2switch.md`, référencée à chaque étape
concernée — pas de duplication entre les deux documents.

---

## Étape 0 — Vérification des fichiers spécifiques au serveur

**À faire avant tout transfert**, sans exception. Voir
`DEPLOIEMENT_o2switch.md` §3 sexies pour le détail complet. Checklist :

- [ ] `.htaccess` : bloc Passenger du serveur identifié et préservé (jamais
      écrasé par la version portable du dépôt).
- [ ] `passenger_wsgi.py` : correspond bien à l'environnement cible
      (`sys.path`, `DJANGO_SETTINGS_MODULE`) — jamais celui d'un autre
      environnement.
- [ ] `config/settings_formation.py` (ou équivalent par instance) :
      fichier du serveur identifié, à ne jamais écraser.
- [ ] Racine de l'application (cPanel « Setup Python App ») : confirmée
      pour l'environnement cible.

## Étape 1 — Sauvegarde

Avant toute modification (Étape 3 de la Méthodologie de Développement
PSM2S) :

1. Copie renommée, sur le serveur, des fichiers à risque identifiés en
   Étape 0 (ex. `.htaccess.bak-AAAAMMJJ`, `passenger_wsgi.py.bak-AAAAMMJJ`)
   via le Gestionnaire de fichiers cPanel.
2. Archive complète du dossier applicatif (fonction « Compresser » du
   Gestionnaire de fichiers), nommée clairement (ex.
   `backup-<environnement>-avant-<lot>-AAAAMMJJ.zip`).
3. Téléchargement de cette archive en local, hors du serveur (double
   sécurité) — par exemple dans `PSM2S\Sauvegardes\`.

Aucune étape suivante ne commence tant que cette sauvegarde n'est pas
confirmée.

## Étape 2 — Transfert des fichiers

**Méthode actuelle : FTP manuel** (FileZilla ou Gestionnaire de fichiers
cPanel). **Recommandation de fond** (non appliquée à ce jour) : faire
passer chaque plateforme sous `Git Version Control` (cPanel) dès que
possible, pour connaître l'état réel du serveur avec certitude.

**Leçon de L3.1 — transfert complet, jamais un diff ciblé** : tant qu'une
plateforme n'est pas suivie par Git, son état réel peut diverger de tout
commit de référence (dépôts FTP manuels successifs dans le temps). Un
`git diff --name-status <commit>..HEAD` s'est révélé insuffisant : deux
fichiers modifiés de longue date (`Templates/base.html`,
`registre/urls.py`) étaient absents du diff calculé, alors qu'ils
manquaient réellement sur le serveur.

**Règle retenue** : si l'état Git du serveur n'est pas garanti, effectuer
une synchronisation complète des répertoires applicatifs concernés
(`registre/`, `Templates/`, `config/` à l'exception des fichiers
spécifiques au serveur identifiés en Étape 0). Les déploiements par diff
ne sont autorisés que sur des environnements dont l'état est connu et
maîtrisé (par exemple un serveur déployé exclusivement via Git). Formation
et production, aujourd'hui déployées par FTP manuel, relèvent donc du
transfert complet — cette règle sera à réévaluer si ces plateformes
passent un jour sous `Git Version Control` cPanel.

Dossiers/fichiers à transférer (hors fichiers serveur, Étape 0) :
- `registre/` (fichiers `.py` racine + `migrations/` + `management/`)
- `Templates/` (racine + `registre/` + `registration/`)
- `config/` : `__init__.py`, `asgi.py`, `wsgi.py`, `urls.py`, `env.py`,
  `settings.py` — **jamais** `settings_formation.py` (Étape 0).
- Fichier `passenger_wsgi.py` propre à l'environnement (Étape 0) —
  vérifier son contenu avant/après transfert, ne pas transférer celui
  d'un autre environnement même si nommé différemment dans le dépôt
  (`passenger_wsgi.py` / `passenger_wsgi_formation.py` ne coexistent que
  dans Git, jamais sur un même serveur).

## Étape 3 — Variables d'environnement (cPanel)

Voir `DEPLOIEMENT_o2switch.md` §3 bis à §3 quinquies et §4 pour le détail.
Au minimum, avant de redémarrer l'application :
- [ ] `DJANGO_SECRET_KEY` présente (obligatoire, sans fallback).
- [ ] `DJANGO_DEBUG` : absente en production/formation (défaut sûr `False`).
- [ ] `DJANGO_SSL` / `DJANGO_HSTS_SECONDS` : présents seulement si le
      durcissement transport a été explicitement décidé pour cet
      environnement (lot dédié, voir §3 quinquies).

## Étape 4 — Commandes serveur

Via le terminal de l'application Python (cPanel « Setup Python App » →
activation du virtualenv, ou SSH) :

```bash
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py check --deploy
```

`check --deploy` doit être vert, à l'exception des avertissements
explicitement acceptés et documentés pour cet environnement (ex. W004/W008/
W012/W016 tant que `DJANGO_SSL` n'est pas activé — voir
`DEPLOIEMENT_o2switch.md` §3 quinquies). `security.W018` (DEBUG actif) ne
doit **jamais** apparaître.

## Étape 5 — Redémarrage de l'application Passenger

cPanel → « Configurer une Application Python » → bouton « Redémarrer »
(ou `touch tmp/restart.txt` depuis le terminal). Un simple changement de
template ou de `.htaccess` ne nécessite pas de redémarrage — Django et
Apache les relisent à chaque requête.

## Étape 6 — Vérification

Dérouler la **checklist de validation post-déploiement** de
`DEPLOIEMENT_o2switch.md` §6 (sécurité/config, fichiers, fonctionnel,
transport). Ajouter systématiquement, pour toute mise à jour fonctionnelle
comme le Lot 2 Calendrier :
- [ ] Écrans clés testés visuellement (connexion, tableau de bord, et les
      écrans propres au lot déployé).
- [ ] Menu/navigation cohérent avec le code déployé (leçon L3.1 : un lien
      de menu ou une route absente ne remonte pas forcément dans un test
      automatisé si le test ne couvre pas cet écran précis).
- [ ] Périmètre par rôle non régressé (un compte restreint ne voit que
      son périmètre).

## Retour arrière (rollback)

1. Restaurer la sauvegarde de l'Étape 1 (fichiers renommés remis en
   place, ou archive complète ré-extraite).
2. Redémarrer l'application Passenger.
3. Vérifier le retour à l'état antérieur.
4. Diagnostiquer la cause avant toute nouvelle tentative — ne pas
   corriger « au fil de l'eau » sur l'environnement cible (cf. principe de
   correction ciblée de la Méthodologie PSM2S).

---

## Historique

- **v1.0** (04/07/2026, L3.2) : première version, construite à partir du
  déploiement réel L3.1 (resynchronisation de la plateforme formation :
  Phases 1+2 + Lot 2 Calendrier). Trois incidents réels ont directement
  produit les Étapes 0 et 2 de cette procédure.
