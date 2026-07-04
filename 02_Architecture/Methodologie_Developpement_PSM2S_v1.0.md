# Méthodologie de Développement PSM2S

**Version :** 1.0\
**Date :** 02/07/2026

## Objectif

Garantir un développement fiable, traçable et sans régression.

Cette méthodologie constitue le processus officiel de développement de
PSM2S. Toute évolution du projet devra suivre ce processus.

------------------------------------------------------------------------

# Processus de développement

## Phase 1 -- Analyse

-   Analyse du besoin ou de l'anomalie.
-   Identification des risques.
-   Définition du périmètre.

**Validation du Directeur Technique.**

------------------------------------------------------------------------

## Phase 2 -- Architecture

-   Analyse du code existant.
-   Proposition(s) d'architecture.
-   Étude des impacts.
-   Choix de la solution.

**Validation du Directeur Technique.**

------------------------------------------------------------------------

## Phase 3 -- Plan d'exécution

Le Lead Developer présente : - les fichiers concernés ; - les composants
à créer ou modifier ; - les impacts attendus ; - le plan d'intervention.

**Validation du Directeur Technique.**

------------------------------------------------------------------------

## Phase 4 -- Développement

-   Développement limité au périmètre validé.
-   Aucun refactoring non demandé.
-   Aucune modification hors périmètre.

------------------------------------------------------------------------

## Phase 5 -- Tests

-   Tests unitaires.
-   Tests fonctionnels.
-   Tests de non-régression.
-   Vérification des exigences de sécurité.

------------------------------------------------------------------------

## Phase 6 -- Documentation

Mise à jour systématique de : - la documentation technique ; -
l'architecture si nécessaire ; - le CHANGELOG ; - les comptes-rendus
d'audit.

------------------------------------------------------------------------

## Phase 7 -- Revue Technique

Le Directeur Technique vérifie : - la conformité avec l'architecture
validée ; - la qualité du code ; - les résultats des tests ; - la
documentation.

------------------------------------------------------------------------

## Phase 8 -- Validation Finale

Un lot est considéré comme terminé uniquement lorsque les **4 Feux
Verts** sont obtenus.

# Les 4 Feux Verts

-   ✅ Développement terminé.
-   ✅ Tests validés.
-   ✅ Documentation mise à jour.
-   ✅ Commit Git réalisé et vérifié.

Une fois ces quatre validations obtenues, le lot est clôturé et le
suivant peut commencer.

------------------------------------------------------------------------

# Principes de gouvernance

-   Un seul lot actif à la fois.
-   Une seule anomalie traitée à la fois.
-   Aucun développement sans validation d'architecture.
-   Aucun refactoring hors périmètre.
-   Aucun lot clôturé sans documentation.
-   Aucune mise en production sans tests.
-   Aucune évolution sans sauvegarde Git.

------------------------------------------------------------------------

# Gestion des évolutions de la méthodologie

Cette version (v1.0) est la référence officielle.

Toute amélioration future devra être présentée comme une **proposition
d'évolution**.

Aucune règle validée ne sera modifiée en cours de développement. Les
évolutions seront intégrées dans une nouvelle version de la méthodologie
(v1.1, v1.2, v2.0, etc.) après validation.

------------------------------------------------------------------------

**Fin du document**
