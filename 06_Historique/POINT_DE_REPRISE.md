# PSM2S — Point de reprise (document de travail)

Dernière mise à jour : 19/09/2026.

> **Ce document est un instantané historique, pas le point d'entrée du
> projet.** Il vit dans `06_Historique/`, dossier d'archives datées non
> retenu à jour rétroactivement (cf. `Documentation/INDEX.md`). **Pour l'état
> courant et pour reprendre le projet aujourd'hui, commencer par
> `Documentation/INDEX.md`, puis `00_IA/DECISIONS.md`** (registre chronologique
> des décisions, activement tenu à jour) — pas par ce fichier.

## État du projet au 19/09/2026

- ✅ **Phase 1 — Sécurité applicative : CLÔTURÉE.**
- ✅ **Phase 2 — Sécurité de production : CLÔTURÉE (côté code).**
- ✅ **Phase 3 et Phase 4** : calendrier réglementaire, industrialisation,
  tableau de bord Directeur, référentiel Prestataires/CorrespondantLocal
  (P4-L5, clos 05/07/2026), adaptation tablette Android (Chantier 1,
  07/09/2026), ajout de pièce jointe à la création de ticket.
- ✅ **Incident de sécurité SECRET_KEY** (production, 03/09/2026) :
  détecté, corrigé, documenté — voir `DECISIONS.md`.
- ✅ **Décommission de l'ancienne instance de production** (`psm2s_v2`,
  03/09/2026) : sauvegardée puis arrêtée, faute d'usage réel.
- ✅ **Phase 5 ouverte** — P5-L0 (Continuité, sécurité et pérennité du
  projet), clôturé le 19/09/2026 : voir section suivante. P5-L1
  (Contractualisation, tarification et périmètre) analysé
  fonctionnellement, développement non commencé.

Détail complet, décision par décision : `00_IA/DECISIONS.md`.

## P5-L0 — Résultat du crash-test de reprise (19/09/2026)

**Restauration complète de l'instance PSM2S Formation sur un nouveau
poste : RÉUSSIE.**

Le test a porté sur la reconstruction de l'instance à partir des éléments
disponibles : code source, base de données, configuration et fichiers
nécessaires. Après restauration, l'instance a été démarrée et testée
fonctionnellement de manière approfondie par le concepteur ; les
fonctionnalités vérifiées sont opérationnelles.

**Crash-test validé sur l'instance PSM2S Formation** : restauration sur un
nouveau poste, démarrage de l'application et validation fonctionnelle
approfondie réussis. Le test valide la procédure de reprise
(`08_Procedures/PROC-003_Restauration_PSM2S.docx`) d'une instance PSM2S
sur un nouvel environnement.

Le test n'a pas porté sur toutes les configurations possibles de clients
futurs.

Mécanismes de sauvegarde existants, documentés (aucun nouveau système
créé) : sauvegarde de la base de données côté serveur, JetBackup
(hébergeur), et copie ponctuelle externe (archive locale, ex.
`archive_psm2s_v2_avant_arret_20260903.tar.gz`).

## P5-L0 — Autres actions de clôture (19/09/2026)

- Correction de `config/settings_formation.py` : suppression du
  `DEBUG = True` codé en dur, hérite désormais du défaut sûr de
  `settings.py` (`DEBUG=False` sauf `DJANGO_DEBUG=True` explicite en
  environnement).
- Vérification : aucune dépendance de code à `Cle.txt` ni à
  `la derniere clé secret_key.txt` — seuls des documents/scripts
  d'audit y font référence à titre historique. Suppression de ces deux
  fichiers laissée à l'exécution de Phil (hors accès fichier de
  l'assistant), après confirmation que la variable cPanel
  `DJANGO_SECRET_KEY` reste l'unique source active.
- Nettoyage `04_Juridique/` (fichiers étrangers au projet) : à exécuter
  par Phil, même raison.
- Statut de `L3.4.4` (architecture Core/Variantes) fait évoluer :
  **VALIDÉE COMME ORIENTATION ARCHITECTURALE — IMPLÉMENTATION DIFFÉRÉE**
  (aucun développement réalisé, décision d'orientation actée).

## Rappels techniques toujours valables

- Poser `DJANGO_SECRET_KEY` avant toute commande Django en local
  (`$env:DJANGO_SECRET_KEY = "..."`) — à reposer à chaque nouveau terminal.
- Variables d'environnement de production : voir `08_Procedures/DEPLOIEMENT_o2switch.md`.
- Procédures officielles : `PROC-001` (déploiement), `PROC-002`
  (correctif ciblé), `PROC-003` (restauration).

## Méthode (inchangée depuis le début)

Une anomalie / un objectif = un lot. Revue d'architecture (sans code) →
arbitrage DT → sauvegarde → développement → tests → documentation →
validation DT → commit. Toute évolution doit être conforme à
l'Architecture de Production v1, ou justifier un écart.
