# PSM2S - DEVELOPMENT PROTOCOL

## Objectif

Ce document définit la méthode officielle de développement de PSM2S.

Toutes les IA et tous les développeurs doivent respecter ce protocole.

---

# Étape 1 - Comprendre

Avant toute modification :

- Lire START_HERE.md
- Lire IA_RULES.md
- Comprendre l'architecture du projet
- Identifier les modèles Django concernés
- Identifier les vues impactées
- Identifier les templates concernés

Ne produire aucun code.

---

# Étape 2 - Analyse

Présenter uniquement :

- le problème identifié ;
- la solution proposée ;
- les fichiers concernés ;
- les impacts éventuels ;
- les risques techniques.

Attendre la validation.

---

# Étape 3 - Sauvegarde

Avant toute modification :

- vérifier que Git est propre ;
- effectuer un commit si nécessaire ;
- effectuer un git push ;
- vérifier qu'une sauvegarde locale existe.

---

# Étape 4 - Développement

Développer une seule fonctionnalité importante.

Ne jamais développer plusieurs modules simultanément.

Respecter l'architecture existante.

Limiter les modifications au strict nécessaire.

---

# Étape 5 - Vérification

À la fin du développement :

- vérifier que le projet démarre ;
- vérifier les migrations ;
- vérifier les vues ;
- vérifier les modèles ;
- vérifier qu'aucune régression n'a été introduite.

---

# Étape 6 - Validation

Le développement est présenté au Product Owner.

Aucune nouvelle fonctionnalité ne commence avant validation de la précédente.

---

# Règles de qualité

Toujours privilégier :

- simplicité ;
- lisibilité ;
- maintenabilité ;
- performances ;
- réutilisation du code.

Éviter :

- les duplications ;
- les dépendances inutiles ;
- les modifications globales sans justification.

---

# Règle finale

Mieux vaut une fonctionnalité parfaitement terminée que cinq fonctionnalités incomplètes.