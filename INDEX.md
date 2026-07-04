# PSM2S — INDEX de la documentation

Point d'entrée officiel de la documentation PSM2S, créé le 04/07/2026 sur
décision du Directeur Technique. Catalogue **logique** des documents ayant
une valeur durable — n'implique aucun déplacement physique de fichiers.
Les nouveaux documents s'ajoutent ici ; les anciens ne sont pas déplacés.

Pour la gouvernance du comportement IA sur ce projet, voir `00_IA/START_HERE.md`
(point d'entrée spécifique aux assistants IA intervenant sur PSM2S).

## Gouvernance et vision

| Document | Rôle |
|---|---|
| `00_IA/START_HERE.md` | Point d'entrée pour toute IA intervenant sur le projet |
| `00_IA/IA_RULES.md` | Comportement attendu du Lead Developer IA (v2.3) |
| `00_IA/VISION_PRODUIT.md` | Vision produit de PSM2S |
| `00_IA/PRODUCT_BACKLOG.md` | Backlog produit |
| `00_IA/DECISIONS.md` | Registre des décisions actées, par phase/lot |
| `00_IA/DEVELOPMENT_PROTOCOL.md` | Protocole de développement |
| `Methodologie_Developpement_PSM2S_v1.0.md` | Les 8 phases + 4 Feux Verts |

## Architecture et politique produit

| Document | Rôle |
|---|---|
| `POLITIQUE-001_Evolution_Core_Variante_PSM2S.md` | Politique de décision Core/Variante (issue de L3.4) |

## Procédures d'exploitation

| Document | Rôle |
|---|---|
| `PROC-001_Deploiement_Plateforme_PSM2S.md` | Déploiement (nouvelle instance ou mise à jour) |
| `PROC-002_Maintenance_Instance_Client_PSM2S.md` | Correctif ciblé sur une instance déployée |
| `DEPLOIEMENT_o2switch.md` | Référence technique o2switch (variables, checklist) |

## Historique de développement (archives datées)

| Dossier | Contenu |
|---|---|
| `Audits/` | Audits, comptes-rendus de lots Phase 1/2, rapports de clôture |
| `Developpements/` | Architecture et comptes-rendus des lots Phase 3 et Lot 3 |

## Hors périmètre de cet index

Documents commerciaux/légaux (contrat d'abonnement, CGV, annexe RGPD),
supports de communication, captures d'écran du manuel, documents-source du
module DUERP (`DUERP IAB/`). Valeur réelle mais hors documentation
technique/gouvernance de PSM2S.

**Point de vigilance** : `07_ Ressources/la derniere clé secret_key.txt`
contient une valeur sensible en clair — exclu du dépôt Git de sauvegarde
(voir `.gitignore`). À terme, à sortir du dossier vers un gestionnaire de
secrets plutôt qu'un fichier texte, même non versionné.

---

## Décision DT du 04/07/2026 (organisation documentaire)

- Structure actuelle conservée (`00_IA/`, `Audits/`, `Developpements/`,
  racine) — pas de réorganisation physique tant qu'elle n'apporte pas de
  bénéfice concret.
- `INDEX.md` (ce fichier) devient le point d'entrée officiel : les
  nouveaux documents s'y ajoutent au fil de l'eau.
- Réorganisation physique **reportée** au moment où `Documentation/`
  sera elle-même versionnée sous Git (voir dépôt privé de sauvegarde,
  ci-dessous) — un déplacement de fichiers y sera alors réversible via
  l'historique Git, ce qui n'est pas le cas aujourd'hui.
- Sauvegarde : dépôt Git privé séparé, dédié à `Documentation/`,
  distinct du dépôt de code (voir instructions de mise en place fournies
  par le Lead Developer).

*Fichier vivant : ajouter une ligne par nouveau document de référence créé.*
