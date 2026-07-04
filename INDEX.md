# PSM2S — INDEX de la documentation

Point d'entrée officiel de la documentation PSM2S, créé le 04/07/2026 sur
décision du Directeur Technique.

**Mise à jour du 04/07/2026** : adoption de la structure `01_Livre_blanc` à
`08_Procedures` que le DT avait déjà créée mais qui était restée vide et
inutilisée (invisible aux outils de recherche par fichiers tant qu'aucun
fichier n'y était déposé). `Documentation/` étant désormais versionnée
(dépôt privé `psm2s-documentation`), ce déplacement est réversible via
l'historique Git. Les anciens dossiers `Audits/` et `Developpements/`
disparaissent une fois vidés de leur contenu.

## 00_IA — Gouvernance et vision

| Document | Rôle |
|---|---|
| `00_IA/START_HERE.md` | Point d'entrée pour toute IA intervenant sur le projet |
| `00_IA/IA_RULES.md` | Comportement attendu du Lead Developer IA (v2.3) |
| `00_IA/VISION_PRODUIT.md` | Vision produit de PSM2S |
| `00_IA/PRODUCT_BACKLOG.md` | Backlog produit |
| `00_IA/DECISIONS.md` | Registre des décisions actées, par phase/lot |
| `00_IA/DEVELOPMENT_PROTOCOL.md` | Protocole de développement |

## 01_Livre_blanc — Pourquoi PSM2S, tout ce qu'on peut en faire

| Document | Rôle |
|---|---|
| `01_Livre_blanc/Pourquoi mettre en place PSM2S.docx` | Pourquoi ce projet a été créé |
| `01_Livre_blanc/on vas parler de PSM2S.docx` | Présentation générale de PSM2S |
| `01_Livre_blanc/Gemini mon copilote PSM2S.docx` | Récit du développement assisté par IA |

## 02_Architecture — Politique et méthode produit

| Document | Rôle |
|---|---|
| `02_Architecture/POLITIQUE-001_Evolution_Core_Variante_PSM2S.md` | Politique de décision Core/Variante (issue de L3.4) |
| `02_Architecture/Methodologie_Developpement_PSM2S_v1.0.md` | Les 8 phases + 4 Feux Verts |

## 03_Développement — Historique des lots (Phase 3, Lot 3)

Comptes-rendus et architectures des lots Calendrier (Lot 1/2) et
Industrialisation (L3.1 à L3.4), dans l'ordre chronologique de production.

## 04_Juridique

Contrat d'Abonnement PSM2S, Conditions Générales de Vente, Annexe RGPD.

## 05_Commercial

Supports de communication (bannière LinkedIn, logo), documents PBCI,
procédure d'ouverture d'un nouveau client, captures d'écran de démonstration.

## 06_Historique — Audits et clôtures (Phase 1, Phase 2)

Audits techniques, comptes-rendus de correction (IDOR, sécurité de
production), rapports de clôture de Phase 2 et de Lot 3.

## 07_ Ressources

Ressources diverses : établissements virtuels de test, documents-source
DUERP IAB. **Contient un secret en clair** (`la derniere clé secret_key.txt`)
— exclu du dépôt Git de sauvegarde (`.gitignore`), à sortir vers un
gestionnaire de secrets à terme.

## 08_Procedures — Procédures d'exploitation

| Document | Rôle |
|---|---|
| `08_Procedures/PROC-001_Deploiement_Plateforme_PSM2S.md` | Déploiement (nouvelle instance ou mise à jour) |
| `08_Procedures/PROC-002_Maintenance_Instance_Client_PSM2S.md` | Correctif ciblé sur une instance déployée |
| `08_Procedures/DEPLOIEMENT_o2switch.md` | Référence technique o2switch (variables, checklist) |

---

## Principe de mise à jour

Les documents **permanents** (00_IA, 02_Architecture, 08_Procedures) sont
tenus à jour à chaque évolution. Les documents **datés** (`03_Développement`,
`06_Historique`) sont des archives point-dans-le-temps : leurs éventuelles
mentions de chemins ne sont pas rétroactivement corrigées lors d'une
réorganisation — ils décrivent l'état du projet au moment où ils ont été
écrits.

*Fichier vivant : ajouter une ligne par nouveau document de référence créé.*
