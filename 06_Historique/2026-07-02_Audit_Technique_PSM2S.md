# Rapport d'audit technique — PSM2S

Auditeur : Auditeur Technique Senior Django (IA)
Date : 02/07/2026
Périmètre : intégralité du code source (`Code-Source/`) — Django 4.2+, Python 3.9, SQLite, déploiement Passenger/O2switch.
Méthode : revue de code statique en lecture seule. **Aucun fichier modifié, aucun code écrit.**

---

## Synthèse générale

PSM2S est un monolithe Django cohérent et lisible : modèles bien conçus, conventions homogènes, réutilisation correcte des mécanismes Django (ORM, formulaires, templates auto-échappés, middleware CSRF). Le produit est fonctionnellement riche et fidèle à sa vision.

L'application souffre en revanche de **failles de configuration de production critiques** (DEBUG actif, SECRET_KEY en clair, médias confidentiels servis sans authentification) et d'un **contrôle d'accès objet incomplet** : les listes sont filtrées par rôle, mais l'accès direct par identifiant (URL) ne l'est souvent pas. Pour une plateforme hébergeant des PV de commissions de sécurité, des signatures manuscrites et des données RGPD, ces points doivent être traités avant tout nouveau développement fonctionnel.

### Notes globales

| Domaine | Note /100 | Commentaire |
|---|---|---|
| Architecture | 68 | Monolithe simple et assumé, modèles solides ; app unique qui commence à saturer |
| Sécurité | 32 | 4 anomalies critiques de configuration et de contrôle d'accès |
| Qualité | 58 | Code lisible et homogène ; zéro test automatisé |
| Maintenabilité | 52 | views.py monolithique, CSS dupliqué, pas de Git, doublons de logique de droits |
| Performances | 62 | Correct au volume actuel ; N+1 sur le tableau de bord, filtres en Python |
| **Globale** | **54** | Bloquants : sécurité de production et IDOR |

---

## 1. Anomalies CRITIQUES

### C1 — DEBUG activé en production
- **Criticité** : Critique
- **Fichier** : `config/settings.py`, ligne 17 (`DEBUG = True`) ; également `config/settings_formation.py` ligne 26
- **Description** : le mode debug est actif sur un site exposé publiquement (le commentaire « Passer à False en production réelle » n'a jamais été appliqué).
- **Risque** : divulgation complète des stack traces, du paramétrage, des chemins serveur et de fragments de données à tout visiteur provoquant une erreur ; c'est aussi ce qui active le service public des médias (voir C3).
- **Recommandation** : `DEBUG = False` en production, piloté par variable d'environnement ; configurer les pages 404/500 et `ADMINS`/`LOGGING` pour la remontée d'erreurs.
- **Difficulté** : Faible (attention : nécessite de traiter C3 et la desserte des statics avant, sinon le site perd médias et CSS).

### C2 — SECRET_KEY exposée en clair
- **Criticité** : Critique
- **Fichier** : `passenger_wsgi.py`, ligne 3 (clé en dur) ; `config/settings.py` ligne 15 (fallback `django-insecure-…`) ; copies probables dans `passenger_wsgi.py.bak` et `settings.py.bak`
- **Description** : la clé secrète de production est écrite en clair dans le code, dupliquée dans des fichiers .bak, et le fallback du settings est une valeur publique connue.
- **Risque** : quiconque lit le code (sauvegarde, partage, futur dépôt Git) peut forger cookies de session, jetons CSRF et **liens de réinitialisation de mot de passe** → prise de contrôle de comptes.
- **Recommandation** : générer une nouvelle clé, la stocker hors du code (variable d'environnement o2switch ou fichier hors racine à permissions restreintes), supprimer le fallback insecure et les fichiers .bak, invalider les sessions existantes.
- **Difficulté** : Faible.

### C3 — Documents confidentiels servis sans authentification
- **Criticité** : Critique
- **Fichier** : `config/urls.py`, lignes 37-38 (`static(settings.MEDIA_URL, …)`) — actif car DEBUG=True
- **Description** : tout le dossier `/media/` (PV de commissions de sécurité, contrats, rapports, pièces RGPD, **signatures manuscrites** des directeurs) est servi à toute personne non authentifiée connaissant ou devinant l'URL. Les chemins sont prévisibles (`/media/documents/2026/06/<nom du fichier>.pdf` — noms de fichiers conservés).
- **Risque** : fuite de données personnelles et confidentielles (violation RGPD potentielle), réutilisation frauduleuse des images de signature.
- **Recommandation** : servir les médias via une vue Django authentifiée qui vérifie les droits sur l'objet lié (ou X-Sendfile/X-Accel équivalent o2switch), stocker les fichiers hors racine web, renommer les fichiers avec un identifiant non prédictible.
- **Difficulté** : Moyenne.

### C4 — Contrôle d'accès objet incomplet (IDOR généralisé)
- **Criticité** : Critique (écriture) / Élevée (lecture)
- **Fichier** : `registre/views.py`, nombreuses vues
- **Fonctions concernées (non exhaustif)** : `detail_etablissement` (seul le rôle prestataire est vérifié — un directeur ou factotum accède à **n'importe quel** établissement par son ID), `registre_pdf`, `historique_controle`, `carnet_eau`, `detail_visite_commission`, `duerp_detail` / `duerp_checklist` / `duerp_modifier`, `accessibilite_*`, `modifier_document` / `supprimer_document`, `ajouter_piece_jointe` / `supprimer_piece_jointe`, `modifier_ticket`, `modifier_intervention`, `modifier_niveau_factotum` (un directeur peut modifier le niveau d'un factotum d'un autre site).
- **Description** : les vues *listes* filtrent correctement via `_get_etab_ids_autorises`, mais les vues *détail/édition/suppression* font `get_object_or_404(pk)` sans vérifier que l'objet appartient à un établissement autorisé pour l'utilisateur.
- **Risque** : un utilisateur authentifié à faibles privilèges (prestataire, factotum niveau 1) peut lire, modifier ou supprimer des données d'autres établissements en manipulant les identifiants d'URL.
- **Recommandation** : créer un helper unique (ex. « récupérer l'objet ou 404 si établissement non autorisé », s'appuyant sur `_get_etab_ids_autorises`) et l'appliquer systématiquement à toutes les vues à paramètre `pk`/`etab_pk`. Ajouter des tests d'accès par rôle.
- **Difficulté** : Moyenne (mécanique mais transversale, ~40 vues à passer en revue).

---

## 2. Anomalies ÉLEVÉES

### E1 — Mots de passe créés sans validation
- **Criticité** : Élevée
- **Fichier** : `registre/forms.py`, `UtilisateurForm.clean()`/`save()` (lignes ~281-300)
- **Description** : le formulaire vérifie seulement l'égalité des deux saisies ; `validate_password()` n'est jamais appelé, donc les `AUTH_PASSWORD_VALIDATORS` du settings sont inopérants hors admin. Un mot de passe « a » est accepté.
- **Risque** : comptes à mots de passe triviaux sur une application exposée.
- **Recommandation** : appeler `django.contrib.auth.password_validation.validate_password` dans `clean()`.
- **Difficulté** : Faible.

### E2 — `is_staff = True` imposé à tous les utilisateurs
- **Criticité** : Élevée
- **Fichier** : `registre/forms.py`, `UtilisateurForm.save()`, ligne ~296
- **Description** : chaque utilisateur créé/modifié via l'application (y compris prestataires externes) devient membre du staff Django et peut se connecter à `/admin/`.
- **Risque** : surface d'attaque inutile ; combiné à l'attribution de groupes porteurs de permissions de modèle, un prestataire pourrait manipuler des données via l'admin.
- **Recommandation** : réserver `is_staff` aux administrateurs ; le commentaire justificatif (« connexion via /admin/login/ ») ne correspond plus au flux réel (`/connexion/`).
- **Difficulté** : Faible (vérifier qu'aucun flux ne dépend de l'admin, puis nettoyer les comptes existants).

### E3 — Uploads de fichiers non validés
- **Criticité** : Élevée
- **Fichier** : `registre/models.py` (10 `FileField`/`ImageField`) et `registre/forms.py` (aucun validateur)
- **Description** : aucune restriction d'extension, de type MIME ni de taille par fichier (seul `DATA_UPLOAD_MAX_MEMORY_SIZE` global existe). Un fichier `.html` ou `.svg` peut être déposé.
- **Risque** : XSS stocké via `/media/` (le fichier est servi avec son Content-Type deviné), dépôt de contenus arbitraires, saturation disque.
- **Recommandation** : `FileExtensionValidator` (pdf, images, docx…) + contrôle de taille dans les formulaires ; en-tête `Content-Disposition: attachment` à la desserte (à combiner avec C3).
- **Difficulté** : Faible à Moyenne.

### E4 — Cookies et transport non durcis
- **Criticité** : Élevée
- **Fichier** : `config/settings.py` (absents)
- **Description** : `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` ne sont pas définis alors que le site est derrière un proxy HTTPS (`SECURE_PROXY_SSL_HEADER` est, lui, bien configuré).
- **Risque** : cookies de session transmissibles en HTTP clair → vol de session.
- **Recommandation** : activer les quatre réglages ci-dessus en production (avec HSTS progressif).
- **Difficulté** : Faible.

### E5 — Incohérence de droits : `peut_tout_voir` inclut le directeur
- **Criticité** : Élevée
- **Fichier** : `registre/models.py` (`Utilisateur.peut_tout_voir`, ligne ~80) ; consommé par `registre/views.py` `duerp_liste` (ligne ~2017 post-Lot 1)
- **Description** : trois systèmes de droits coexistent (décorateurs `permissions.py`, helpers du modèle, `_get_etab_ids_autorises`) et se contredisent : `_get_etab_ids_autorises` restreint le directeur à ses sites, mais `peut_tout_voir` lui donne « tout » — un directeur voit ainsi les DUERP de **tous** les établissements.
- **Risque** : fuite d'informations inter-établissements ; règles d'accès imprévisibles selon l'écran.
- **Recommandation** : faire de `_get_etab_ids_autorises` la source unique de vérité, aligner ou supprimer `peut_tout_voir`/`peut_voir_etablissement`.
- **Difficulté** : Moyenne.

### E6 — SQLite en production multi-utilisateurs, base dans l'arborescence applicative
- **Criticité** : Élevée
- **Fichier** : `config/settings.py` lignes 82-87 ; fichier `db.sqlite3` présent à la racine du projet
- **Description** : base SQLite unique pour une application multi-sites multi-rôles avec écritures concurrentes (tickets, réalisations, cron d'alertes), stockée au milieu du code déployé, sans stratégie de sauvegarde visible.
- **Risque** : erreurs « database is locked », corruption/perte lors de déploiements, aucune reprise après sinistre.
- **Recommandation** : migrer vers MySQL/MariaDB (disponible o2switch) ou a minima déplacer la base hors racine, activer le mode WAL et mettre en place des sauvegardes planifiées testées.
- **Difficulté** : Moyenne.

---

## 3. Anomalies MOYENNES

### M1 — XSS réfléchi dans la vue de diagnostic email
- **Criticité** : Moyenne (atténuée par `@admin_requis`)
- **Fichier** : `registre/views.py`, `test_email` (lignes ~767-807)
- **Description** : le paramètre GET `dest` et le message d'erreur sont injectés dans du HTML construit par f-string et renvoyé via `HttpResponse`, sans échappement.
- **Risque** : XSS réfléchi ciblant un administrateur connecté (via lien piégé).
- **Recommandation** : échapper les valeurs (`django.utils.html.escape`) ou passer par un template.
- **Difficulté** : Faible.

### M2 — Effets de bord déclenchés par GET
- **Criticité** : Moyenne
- **Fichier** : `registre/views.py`, `lancer_alertes` et `test_email`
- **Description** : l'envoi réel d'emails est déclenché par une simple requête GET, sans confirmation POST ni protection CSRF applicable.
- **Risque** : envois massifs involontaires (pré-chargement navigateur, lien piégé, robot).
- **Recommandation** : exiger POST + confirmation pour l'exécution réelle.
- **Difficulté** : Faible.

### M3 — Copie de signature par chemin relatif
- **Criticité** : Moyenne
- **Fichier** : `registre/views.py`, `_copier_signature` (lignes ~2547-2558)
- **Description** : écrit via `os.path.join('media', …)` relatif au répertoire courant du process, en contournant l'API de storage Django, sans gestion d'erreur.
- **Risque** : fichiers écrits au mauvais endroit selon le cwd de Passenger/cron ; signature « posée » mais introuvable.
- **Recommandation** : utiliser `default_storage.save()` / `MEDIA_ROOT`.
- **Difficulté** : Faible.

### M4 — Ticket créé sans description (champ requis absent du formulaire)
- **Criticité** : Moyenne
- **Fichier** : `registre/forms.py`, `TicketTravauxForm.Meta.fields` (lignes ~54-61) vs `registre/models.py` `TicketTravaux.description` (non blank)
- **Description** : le champ `description`, obligatoire au modèle, n'est pas dans le formulaire : les tickets créés dans l'application ont une description vide (chaîne vide insérée sans validation).
- **Risque** : données incomplètes, emails de notification sans contenu, incohérence avec l'admin qui l'exige.
- **Recommandation** : réintégrer `description` au formulaire ou l'assumer `blank=True` au modèle.
- **Difficulté** : Faible.

### M5 — N+1 et double requêtage sur le tableau de bord multi-sites
- **Criticité** : Moyenne
- **Fichier** : `registre/views.py`, `tableau_de_bord` (boucle lignes ~1451-1523)
- **Description** : par établissement, requêtes `Prescription.count()` et **deux** requêtes `Contrat` (dont une redondante pour les alertes) ; les compteurs de contrôles sont calculés en Python sur des listes.
- **Risque** : dégradation linéaire avec le nombre de sites (déjà ~30 requêtes superflues pour 15 sites) sur l'écran le plus consulté.
- **Recommandation** : annotations (`Count`, `Q`) et pré-agrégations en une passe.
- **Difficulté** : Moyenne.

### M6 — Filtres et compteurs évalués en Python plutôt qu'en SQL
- **Criticité** : Moyenne
- **Fichier** : `registre/views.py`, `controles_global` (lignes ~441-453) — `nb_retard = sum(1 for c in qs_base)` charge toute la table ; filtres `a_faire`/`retard`/`categorie` par compréhensions de listes
- **Risque** : montée en charge médiocre ; logique « en retard » dupliquée entre SQL et Python.
- **Recommandation** : exprimer `est_en_retard` en filtre queryset (comme le fait déjà `tableau_de_bord` pour `qs_retard`) et compter en base.
- **Difficulté** : Faible.

### M7 — Compteur global non filtré par rôle sur le dashboard
- **Criticité** : Moyenne
- **Fichier** : `registre/views.py`, `dashboard` (lignes ~296-298, `tickets_urgents`)
- **Description** : le compteur de tickets urgents est calculé sur **tous** les établissements, y compris pour un directeur/factotum/prestataire restreint.
- **Risque** : fuite d'information mineure et chiffre incohérent avec la liste affichée.
- **Recommandation** : appliquer le même filtre `etab_ids` que le reste de la vue.
- **Difficulté** : Faible.

### M8 — Dépendances non épinglées et inutilisées
- **Criticité** : Moyenne
- **Fichier** : `requirements.txt`
- **Description** : `django>=4.2` sans borne haute ; `gunicorn` et `whitenoise` déclarés mais inutilisés (Passenger sert l'app ; whitenoise absent du MIDDLEWARE).
- **Risque** : mise à jour majeure non maîtrisée lors d'un `pip install`, dépendances mortes trompeuses.
- **Recommandation** : épingler (`Django==4.2.x`), ajouter `openpyxl` (requis par `import_excel.py`), retirer l'inutilisé ou activer whitenoise pour remplacer la desserte `static()`.
- **Difficulté** : Faible.

### M9 — Absence totale de tests automatisés
- **Criticité** : Moyenne (Élevée au regard du domaine réglementaire)
- **Fichier** : `registre/tests.py` (vide, 3 lignes)
- **Description** : aucune couverture — ni sur le calcul d'échéances, ni sur les droits d'accès, ni sur les alertes.
- **Risque** : régressions silencieuses sur des fonctions de conformité réglementaire ; le protocole d'Étape 5 repose sur des vérifications manuelles.
- **Recommandation** : commencer par les fonctions pures (`_calculer_prochaine_echeance`, `_couleur_conformite`, `calculer_statut` des analyses d'eau) puis des tests d'accès par rôle sur chaque vue (directement liés à C4).
- **Difficulté** : Moyenne (effort continu).

### M10 — `views.py` monolithique et imports dispersés
- **Criticité** : Moyenne
- **Fichier** : `registre/views.py` (~2700 lignes)
- **Description** : toutes les fonctionnalités dans un seul fichier ; imports en milieu de fichier (lignes ~2007, ~2308, ~2545, ~2673), double import de `TypeControle` (lignes 7 et 19), sections dupliquées.
- **Risque** : coût de compréhension croissant, conflits d'édition, risque d'erreur à chaque ajout.
- **Recommandation** : éclater en modules par domaine (`views/registre.py`, `views/duerp.py`, `views/accessibilite.py`…) sans changer les URLs.
- **Difficulté** : Moyenne.

### M11 — Double décorateur `@classmethod` sur `DroitSignature.peut_signer`
- **Criticité** : Moyenne
- **Fichier** : `registre/models.py`, lignes 1347-1348
- **Description** : `@classmethod` appliqué deux fois. Fonctionne par accident sur Python 3.9 (chaînage de descripteurs), mais ce comportement a été retiré des versions récentes de Python.
- **Risque** : rupture silencieuse de **tout le circuit de signature** lors d'une future montée de version Python.
- **Recommandation** : supprimer le décorateur dupliqué.
- **Difficulté** : Faible (une ligne).

### M12 — Alerte email : statut filtré inexistant et échecs silencieux
- **Criticité** : Moyenne
- **Fichier** : `registre/management/commands/envoyer_alertes.py`, ligne 63 (`'en_cours'` n'existe pas dans `ControleEtablissement.STATUT_CHOICES`) ; `fail_silently=True` dans `_notifier_responsable` et `_notifier_nouveau_document` (views.py)
- **Description** : valeur de filtre morte (sans effet mais trompeuse) ; les échecs d'envoi de notifications sont avalés sans journalisation.
- **Risque** : croyance erronée que des alertes partent ; diagnostic impossible.
- **Recommandation** : nettoyer le filtre ; journaliser les échecs (logger dédié) au lieu de `fail_silently`.
- **Difficulté** : Faible.

### M13 — Écrasement silencieux de l'échéance saisie manuellement
- **Criticité** : Moyenne (cohérence fonctionnelle)
- **Fichier** : `registre/views.py`, `modifier_controle` (recalcul lignes ~614-621) vs `ControleEtablissementForm` qui expose `prochaine_echeance`
- **Description** : l'utilisateur peut saisir une échéance dans le formulaire, mais si une date de réalisation et une périodicité existent, sa saisie est écrasée sans message.
- **Risque** : incompréhension utilisateur, échéances « qui ne se laissent pas corriger » (exemple : contrôle décalé réglementairement).
- **Recommandation** : trancher — champ en lecture seule quand le calcul s'applique, ou priorité à la saisie manuelle avec indication visuelle.
- **Difficulté** : Faible.

### M14 — Hygiène du dossier déployé et absence de gestion de versions
- **Criticité** : Moyenne
- **Fichier** : racine `Code-Source/` — `passenger_wsgi.py.bak`, `config/settings.py.bak`, `__pycache__/` multiples, `db.sqlite3`, `logs/`, `media/`, `import_excel.py`, fichiers HTML de documentation mêlés au code ; **aucun dépôt Git détecté**
- **Description** : artefacts de travail, secrets et données vivantes cohabitent avec le code, sans versionnage.
- **Risque** : fuite de secrets via les .bak, écrasements sans retour arrière, déploiements non reproductibles ; l'Étape 3 du protocole (Git propre + push) est inapplicable en l'état.
- **Recommandation** : initialiser Git avec un `.gitignore` (db, media, logs, __pycache__, .bak), sortir données et secrets de l'arborescence code.
- **Difficulté** : Faible à Moyenne.

---

## 4. Anomalies FAIBLES

- **F1** — `registre/models.py` l.485 : `TicketTravaux.cloturer(self, utilisateur)` — paramètre `utilisateur` jamais utilisé (traçabilité de clôture perdue). Correction : Faible.
- **F2** — `registre/views.py` `duerp_supprimer_signature` : ligne `user = request.user` dupliquée (code mort). Correction : Faible.
- **F3** — `registre/models.py` : bannière « MODULE DUERP » dupliquée (l.1090-1093) ; clé de choix non-ASCII `'signalétique'` dans `EvaluationZone.ZONE_CHOICES` (fragile pour URLs/CSS/comparaisons). Correction : Faible (attention migration de données pour la clé).
- **F4** — `config/settings.py` : double entrée TEMPLATES `templates`/`Templates` (compatibilité casse) — fonctionne mais fragile lors d'une migration d'hébergement sensible à la casse. Correction : Faible.
- **F5** — Emojis dans les `choices` de statut (modèles) : mélange présentation/données, complique exports et recherches. Correction : Moyenne (migrations d'affichage).
- **F6** — `.htaccess` quasi vide : aucune règle de protection complémentaire (ex. blocage direct de `db.sqlite3`, en-têtes). Correction : Faible.
- **F7** — CSS massif dupliqué : styles redéfinis dans chaque template via `extra_style` au lieu d'un fichier statique commun versionné/cachable. Correction : Moyenne.
- **F8** — Duplication de logique entre `detail_etablissement` et `registre_pdf` (calcul `annees_dispo`, groupement par catégorie) — à factoriser. Correction : Faible.
- **F9** — `InterventionForm` : liste des tickets non filtrée par les établissements autorisés de l'utilisateur (divulgation de titres de tickets d'autres sites dans le menu déroulant). Correction : Faible (rejoint C4).
- **F10** — Aucune configuration `LOGGING` : erreurs applicatives invisibles hors console Passenger. Correction : Faible.
- **F11** — Pas de limitation de tentatives de connexion (throttling/lockout) sur `/connexion/` et `/admin/`. Correction : Moyenne (django-axes ou équivalent).
- **F12** — `admin.py` : `UtilisateurAdmin` n'expose ni `niveau_factotum` ni `signature` (gestion incomplète depuis l'admin). Correction : Faible.

---

## 5. Lecture par domaine demandé

**1. Architecture générale** — Monolithe une-app assumé et adapté à la taille du projet ; modèles riches et bien nommés ; séparation nette modèles/vues/templates. Points faibles : `views.py` unique (M10), trois systèmes de droits parallèles (E5), configuration production/dev non séparée (C1, `settings_formation.py` hérite du DEBUG).

**2. Sécurité Django** — DEBUG : C1. SECRET_KEY : C2. ALLOWED_HOSTS : correctement restreint ✓. CSRF : middleware actif, `{% csrf_token %}` présent, logout en POST ✓ ; effets de bord GET : M2. XSS : templates auto-échappés ✓ sauf M1 ; risque via uploads : E3. SQL Injection : ORM exclusivement, aucune requête brute — RAS ✓. Permissions : décorateurs par rôle corrects mais IDOR généralisé : C4, E5. Authentification : flux standard ✓, mots de passe non validés : E1, `is_staff` global : E2, pas de throttling : F11. Sessions/Cookies : moteur standard ✓, flags Secure/HSTS absents : E4. Upload : E3 + desserte anonyme C3.

**3. Qualité du code** — Lisible, commenté en français, conventions homogènes, docstrings utiles. Défauts : code mort (F1, F2), double décorateur (M11), champ requis absent d'un formulaire (M4), aucune couverture de tests (M9).

**4. Dette technique** — Pas de Git (M14), .bak et artefacts déployés (M14), dépendances non épinglées (M8), duplication de logique de droits (E5) et d'écrans (F8), CSS dupliqué (F7), SQLite (E6).

**5. Performances** — Volume actuel maîtrisé ; requêtes bornées et `select_related` présents sur les écrans récents ✓. À corriger : N+1 du tableau de bord (M5), comptage Python (M6), absence de cache statique (F7). Aucun index manquant flagrant (index présents sur RealisationControle ✓).

**6. Maintenabilité** — Bonne cohérence de style ; freinée par le monolithe de vues (M10), l'absence de tests (M9) et de versionnage (M14).

**7. Bonnes pratiques Django** — Respectées : ORM, formulaires, `AUTH_USER_MODEL` dès l'origine, migrations propres, commande de management pour le cron, messages framework. Écarts : desserte `static()` en production (C3), validation mot de passe contournée (E1), storage contourné (M3), settings non splittés (C1).

**8. Cohérence fonctionnelle** — Écarts relevés : droits directeur incohérents entre écrans (E5, C4), compteur non filtré (M7), échéance manuelle écrasée (M13), tickets sans description (M4), statut d'alerte inexistant (M12), signature « admin compte comme directeur » dans `duerp_signer` (logique de rôle approximative, à spécifier).

---

## 6. Priorisation recommandée (aucune correction effectuée)

1. **Immédiat (avant tout nouveau développement)** : C2 (rotation SECRET_KEY), C1 (DEBUG off, avec desserte statics/médias préparée), C3 (médias authentifiés), E4 (cookies).
2. **Court terme** : C4 + E5 (helper d'autorisation unique + revue des ~40 vues), E1, E2, E3.
3. **Moyen terme** : E6 (base de données), M5/M6 (performances), M9 (tests, en commençant par les droits d'accès), M14 (Git).
4. **Fond de roulement** : M10 (découpage vues), F7 (CSS commun), et le reste des anomalies Faibles.

---

*Rapport établi en lecture seule le 02/07/2026. Les numéros de lignes sont donnés à titre indicatif sur la version du code auditée ce jour (incluant le Lot 1 Calendrier).*
