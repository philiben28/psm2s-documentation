# P5-L1 — Lot C1 : proposition technique (pour validation DT avant développement)

Fait suite à `2026-09-21_P5-L1_Lot_C1_Analyse_Architecture.md` et à la
revue DT du 21/09/2026 (consignée dans `DECISIONS.md`). **Aucun code,
aucune migration.** Intègre les trois points stabilisés :

1. Le `gestionnaire_contractuel` voit le signal `statut_coherent` sur
   son propre contrat (comme admin/responsable_securite).
2. `contrat_historique` sans aucun `ContratCommercial` → redirection
   vers `commercial_accueil`.
3. Aucun lien vers une fonctionnalité C2 (« créer le premier contrat »)
   dans C1.

Trois vues, toutes en lecture seule (GET uniquement, aucun formulaire,
aucune écriture) : `commercial_accueil`, `contrat_detail`,
`contrat_historique`.

---

## 1. `commercial_accueil`

**URL** : `/commercial/` → `registre:commercial_accueil`
**Décorateur** : `gestionnaire_requis` (inchangé, existant)

**Requête** :
```
contrat_actif = ContratCommercial.objects.filter(statut='ACTIF').first()
```
Si trouvé → `redirect('registre:contrat_detail', pk=contrat_actif.pk)`
(pas de rendu de template dans ce cas — l'accueil n'est qu'un routeur
quand un contrat actif existe).

Sinon :
```
dernier_contrat = ContratCommercial.objects.order_by('-date_creation').first()
```
(`None` si aucun `ContratCommercial` n'a jamais existé.)

**Contexte transmis au template** :

| Clé | Contenu |
|---|---|
| `dernier_contrat` | `ContratCommercial` ou `None` |

**Template** : `registre/commercial/accueil.html`. Logique d'affichage
entièrement pilotée par `dernier_contrat` (`None` ou pas) et par les
propriétés de rôle déjà disponibles dans tout gabarit PSM2S
(`user.peut_tout_voir`, etc. — aucune nouvelle variable de contexte
nécessaire pour le rôle, déjà accessible via `request.user`) :

- `dernier_contrat is None` → « Aucun contrat commercial n'a encore été
  créé. » (admin/responsable_securite) ou message informatif minimal
  (directeur).
- `dernier_contrat` existe → « Aucun contrat actif. Dernier contrat
  connu : » + lien vers `contrat_detail` (`dernier_contrat.pk`).
- **Aucun lien vers `renouvellement_form`** dans les deux cas (point 3
  stabilisé) — à ajouter uniquement au moment de C2.

---

## 2. `contrat_detail`

**URL** : `/commercial/contrat/<int:pk>/` → `registre:contrat_detail`
**Décorateur** : `gestionnaire_requis`

**Requête** :
```
contrat = get_object_or_404(ContratCommercial, pk=pk)
```
Pas de vérification de périmètre supplémentaire à ce stade —
`gestionnaire_requis` exclut déjà factotum/prestataire, et
l'existence d'un `ContratCommercial` n'est un secret pour personne
(cohérent avec le patron redirection déjà tranché au Lot B, pas de
`get_*_ou_404` à créer ici).

**Différenciation par rôle — réutilise directement
`gestion_contrat_autorisee(user, contrat)` (Lot B)**, plutôt qu'une
nouvelle vérification ad hoc : cette fonction retourne déjà exactement
« admin, responsable_securite, ou gestionnaire désigné de CE contrat »
— exactement l'ensemble de rôles qui, après l'arbitrage du 21/09,
doivent voir agrégats et signal. Un seul booléen pilote donc les deux
blocs (agrégats + signal), pas deux vérifications séparées :

```
acces_intégral = gestion_contrat_autorisee(request.user, contrat)
```

**Si `acces_intégral`** (admin/responsable_securite/gestionnaire) :
```
aujourd_hui = timezone.now().date()
perimetre = perimetre_a_date(contrat, aujourd_hui)
```
Contexte ajouté :

| Clé | Contenu |
|---|---|
| `peut_voir_agregats` | `True` |
| `nb_etablissements` | `len(perimetre['etablissements'])` |
| `nb_batiments` | `len(perimetre['batiments'])` |
| `montant_mensuel` | `tarif_mensuel(contrat, aujourd_hui)` |
| `signal_statut` | `statut_coherent(contrat, aujourd_hui)` — `None` ou message (arbitrage n°1) |
| `peut_voir_historique` | `True` |

**Sinon** (directeur non gestionnaire — factotum/prestataire déjà
exclus par le décorateur) :
```
etab_ids = etablissements_autorises(request.user) or set()
perimetre = perimetre_a_date(contrat, aujourd_hui)
mes_etablissements_ids = perimetre['etablissements'] & etab_ids
mes_batiments_ids = {
    b.id for b in Batiment.objects.filter(
        id__in=perimetre['batiments'], etablissement_id__in=etab_ids
    )
}
```
Contexte ajouté :

| Clé | Contenu |
|---|---|
| `peut_voir_agregats` | `False` |
| `mes_etablissements` | `Etablissement.objects.filter(id__in=mes_etablissements_ids)` — pour affichage nominatif (architecture §4.1 : « depuis quand », etc. — le « depuis quand » précis par établissement demanderait de rejouer les mouvements un par un ; **point d'implémentation, pas un enjeu d'architecture**, laissé au détail du développement) |
| `ma_part_facture` | `len(mes_etablissements_ids) * contrat.tarif_etablissement_mensuel + len(mes_batiments_ids) * contrat.tarif_batiment_mensuel` |
| `peut_voir_historique` | `False` (jamais de lien vers `contrat_historique` pour ce rôle — cohérent avec `verifier_acces_gestion_contrat` qui le refuserait de toute façon) |
| `signal_statut` | absent du contexte (pas seulement `None` — la clé n'existe pas, pour qu'un template qui l'afficherait par erreur échoue plutôt que d'afficher silencieusement rien) |

**Champs globaux** (durée, dates, statut, tarifs unitaires,
maintenance unitaire) : accessibles directement via `contrat.*` dans le
template, pour tous les rôles atteignant la vue — aucune logique
supplémentaire, déjà les mêmes pour tout le monde (architecture §4.1).

**Template** : `registre/commercial/contrat_detail.html`, un bloc
conditionnel `{% if peut_voir_agregats %}` pour les deux blocs
mutuellement exclusifs.

---

## 3. `contrat_historique`

**URL** : `/commercial/contrat/historique/` →
`registre:contrat_historique`
**Décorateur** : `gestionnaire_requis`, puis vérification manuelle
(pas un simple décorateur, car le contrat de référence doit d'abord
être déterminé) :

```
contrat_reference = (
    ContratCommercial.objects.filter(statut='ACTIF').first()
    or ContratCommercial.objects.order_by('-date_creation').first()
)
if contrat_reference is None:
    return redirect('registre:commercial_accueil')  # arbitrage n°2

refus = verifier_acces_gestion_contrat(request.user, contrat_reference)
if refus:
    return refus
```

Résout explicitement la question laissée ouverte dans l'analyse
(contre quel contrat vérifier l'accès à une vue sans `pk`) : le contrat
`ACTIF` s'il existe, sinon le plus récent créé — jamais aucun contrat
dans ce cas précis, la redirection de l'arbitrage n°2 s'applique avant
même d'atteindre cette vérification.

**Reconstitution de la chaîne** (aucune nouvelle requête complexe —
`contrat_precedent` est déjà une FK directe, Lot A) :
```
contrats = []
courant = contrat_reference
while courant is not None:
    contrats.append(courant)
    courant = courant.contrat_precedent
```

**Contexte transmis au template** :

| Clé | Contenu |
|---|---|
| `contrats` | Liste `ContratCommercial`, du plus récent au plus ancien |

**Template** : `registre/commercial/contrat_historique.html`. Chaque
ligne renvoie vers `contrat_detail` (`{% url 'registre:contrat_detail' pk=c.pk %}`).

---

## 4. Templates — récapitulatif

Sous-dossier dédié (déjà recommandé au Lot C, pour éviter toute
confusion avec `Contrat` prestataire) :

- `Templates/registre/commercial/accueil.html`
- `Templates/registre/commercial/contrat_detail.html`
- `Templates/registre/commercial/contrat_historique.html`

Aucun formulaire dans ces trois templates (vues en lecture seule) —
pas de `{% csrf_token %}` nécessaire, pas de `forms.py` à modifier pour
ce lot.

---

## 5. Tests à prévoir

Nouvelle classe `CommercialConsultationTests` (ou trois classes, une
par vue — détail laissé au développement), fixture reprenant
`BaseGestionContrat` (Lot B, déjà tous les rôles/rattachements
nécessaires) :

| Test | Vue | Vérifie |
|---|---|---|
| `test_accueil_redirige_si_contrat_actif` | `commercial_accueil` | Redirection directe vers `contrat_detail` quand un contrat `ACTIF` existe |
| `test_accueil_aucun_contrat_jamais_cree` | `commercial_accueil` | Message « aucun contrat créé », `dernier_contrat` est `None` |
| `test_accueil_dernier_contrat_non_actif` | `commercial_accueil` | Message + lien vers le dernier contrat connu (`EN_ATTENTE`/`RESILIE`) |
| `test_accueil_aucun_lien_vers_renouvellement` | `commercial_accueil` | Le HTML rendu ne contient aucune URL `renouvellement_form` (non-régression, point 3) |
| `test_detail_admin_voit_agregats_et_signal` | `contrat_detail` | `peut_voir_agregats=True`, `signal_statut` présent dans le contexte |
| `test_detail_gestionnaire_voit_agregats_et_signal` | `contrat_detail` | Idem pour le `gestionnaire_contractuel` du contrat — **test direct de l'arbitrage n°1** |
| `test_detail_directeur_non_gestionnaire_ne_voit_pas_agregats` | `contrat_detail` | `peut_voir_agregats=False`, `signal_statut` absent du contexte |
| `test_detail_directeur_non_gestionnaire_voit_sa_part` | `contrat_detail` | `mes_etablissements`/`ma_part_facture` corrects, limités à son périmètre |
| `test_detail_directeur_hors_perimetre_ne_voit_rien_de_letablissement_dautrui` | `contrat_detail` | Un établissement hors périmètre n'apparaît jamais dans `mes_etablissements` |
| `test_detail_factotum_refuse` | `contrat_detail` | Redirection (`gestionnaire_requis`) |
| `test_historique_chaine_dans_le_bon_ordre` | `contrat_historique` | `contrats` du plus récent au plus ancien, via `contrat_precedent` |
| `test_historique_refuse_directeur_non_gestionnaire` | `contrat_historique` | Redirection (`verifier_acces_gestion_contrat`) |
| `test_historique_redirige_si_aucun_contrat` | `contrat_historique` | Redirection vers `commercial_accueil` — **test direct de l'arbitrage n°2** |
| `test_historique_verifie_contre_le_bon_contrat` | `contrat_historique` | Un gestionnaire du contrat `ACTIF` accède à l'historique même si un contrat plus ancien de la chaîne avait un gestionnaire différent |

Non-régression : suite complète rejouée, `manage.py check`,
`makemigrations --check --dry-run` (aucun changement de modèle attendu
pour C1).

---

## Aucun nouveau point signalé

Les trois points remontés dans l'analyse C1 sont désormais stabilisés
(DT, 21/09/2026) et intégrés ci-dessus. Cette proposition n'a fait
apparaître aucune nouvelle ambiguïté fonctionnelle — uniquement des
détails d'implémentation sans enjeu métier, signalés comme tels
lorsqu'ils apparaissent (§2, « depuis quand » par établissement).

Aucune modification de code n'a été effectuée pour produire ce document.
