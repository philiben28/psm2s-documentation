# P5-L1 — Lot C4 — Proposition technique
## Validation / rejet des demandes d'avenant, génération des `MouvementPerimetre`

Statut : proposition technique, aucun code modifié, aucun commit. Fait
suite à `2026-09-24_P5-L1_Lot_C4_Analyse_Architecture.md`, aux six
arbitrages DT du 24/09/2026 (`DECISIONS.md`, section « Lot C4 ») et aux
deux arbitrages complémentaires du même jour (« Arbitrages
complémentaires du 24/09/2026 », suite à la première version de cette
proposition) — restitués intégralement ci-dessous à chaque section
concernée. **Tous les points sont désormais tranchés.**

**Aucun changement de modèle, aucune migration** : tous les champs
nécessaires existent depuis le Lot A (21/09/2026).

---

## 1. Vues

Deux vues, symétriques à `resiliation_form` (Lot C2) dans leur patron
d'accès, mais distinctes l'une de l'autre (contrairement à
`demande_avenant_form`, la validation et le rejet n'ont pas la même
forme d'entrée utilisateur — l'une ne demande rien, l'autre exige un
motif).

### 1.1 `demande_avenant_valider(request, pk)`

```python
@gestionnaire_requis
def demande_avenant_valider(request, pk):
    demande = get_object_or_404(DemandeAvenant, pk=pk)
    refus = verifier_acces_gestion_contrat(request.user, demande.contrat_commercial)
    if refus:
        return refus
    ...
```

**GET** — écran de confirmation, jamais d'écriture :
- Si `demande.statut != 'EN_ATTENTE'` : affiche un message explicite
  (« Cette demande a déjà été traitée — statut actuel :
  « {statut} ». »), pas de bouton d'action. Même patron que
  `activer_contrat.html`/`motif_refus`.
- Si `demande.contrat_commercial.statut != 'ACTIF'` : affiche un
  message explicite (« Cette demande n'est plus validable : le contrat
  concerné n'est plus actif (statut actuel : « {statut} »). »),
  **aucun bouton de confirmation** — cohérent avec l'arbitrage n°2
  (refus systématique, jamais d'écriture, jamais de rejet automatique).
  Réutilise le même texte que le bandeau déjà affiché en lecture seule
  sur `demande_avenant_liste.html` depuis C3, pour ne jamais dire deux
  choses différentes sur le même fait.
- Sinon : écran de confirmation nominal, réutilisant `perimetre_a_date`
  et `tarif_mensuel` (aucune nouvelle fonction de calcul) pour afficher
  le même récapitulatif « avant/après » que celui déjà vu par le
  demandeur à la soumission (C3, §4.4 de l'architecture) — établissements
  et bâtiments ajoutés/retirés, impact tarifaire. Montants **toujours**
  visibles ici (contrairement à C3) : atteindre cette vue suppose déjà
  d'être gestionnaire du contrat (`verifier_acces_gestion_contrat`), la
  restriction C1/C3 sur les agrégats ne s'applique donc pas — cohérent,
  pas un nouvel écart.
  - Si `demande.date_effet_souhaitee < aujourd'hui` : bandeau
    d'avertissement explicite (« La date d'effet souhaitée,
    {date}, est déjà passée. »), **sans bloquer le bouton de
    confirmation** — conforme à l'arbitrage n°4. Un seul geste de
    confirmation suffit (pas de case à cocher séparée) : l'avertissement
    est visible sur le même écran que le bouton
    `[Confirmer la validation]`, cohérent avec le patron déjà utilisé
    par `activer_contrat.html` (nommer l'effet avant de le confirmer,
    un seul bouton).

**POST** — écriture, dans une transaction unique :

```python
    from django.db import transaction
    with transaction.atomic():
        demande = get_object_or_404(
            DemandeAvenant.objects.select_for_update(), pk=pk
        )
        if demande.statut != 'EN_ATTENTE':
            messages.error(request, "Cette demande a déjà été traitée.")
            return redirect('registre:demande_avenant_liste')

        contrat = get_object_or_404(
            ContratCommercial.objects.select_for_update(),
            pk=demande.contrat_commercial_id,
        )
        if contrat.statut != 'ACTIF':
            messages.error(
                request,
                "Cette demande n'est plus validable : le contrat "
                f"concerné n'est plus actif (statut actuel : "
                f"« {contrat.get_statut_display()} »)."
            )
            return redirect('registre:demande_avenant_liste')

        demande.statut = 'VALIDEE'
        demande.validateur = request.user
        demande.date_traitement = timezone.now()
        demande.save()

        for ligne in demande.lignes.all():
            MouvementPerimetre.objects.create(
                contrat_commercial=contrat,
                type_mouvement=ligne.type_mouvement,
                type_objet=ligne.type_objet,
                etablissement=ligne.etablissement,
                batiment=ligne.batiment,
                date_effet=demande.date_effet_souhaitee,
                auteur=request.user,
                ligne_demande_origine=ligne,
            )

    messages.success(request, "Demande validée, périmètre mis à jour.")
    return redirect('registre:demande_avenant_liste')
```

Points notables :
- **Revérification après verrou** (arbitrage n°5) : `demande.statut` et
  `contrat.statut` sont relus **après** acquisition des deux verrous,
  jamais avant — les valeurs lues avant `select_for_update()` (utilisées
  seulement pour l'écran GET) ne sont jamais réutilisées pour décider de
  l'écriture.
- **Aucun rejet automatique** (arbitrage n°2) : le bloc `if contrat.statut
  != 'ACTIF'` se contente d'un message et d'une redirection — aucune
  écriture sur `demande`, qui reste `EN_ATTENTE`.
- La permission (`verifier_acces_gestion_contrat`) est vérifiée une
  première fois avant le `POST` (comme pour toute vue Django classique),
  **pas** re-vérifiée une seconde fois à l'intérieur de la transaction —
  contrairement au statut, la désignation du `gestionnaire_contractuel`
  n'est pas protégée par le verrou (elle n'est pas retenue dans son
  historique) et sa modification concurrente est un cas suffisamment
  rare et sans conséquence sur l'intégrité du périmètre (contrairement à
  la double activation, qui est le risque réel visé par les verrous)
  pour ne pas justifier une revérification supplémentaire. Détail mineur
  signalé au DT dans le bilan (pas un point bloquant) — la proposition
  part de ce principe sauf préférence contraire pour une revérification
  systématique.

### 1.2 `demande_avenant_rejeter(request, pk)`

```python
@gestionnaire_requis
def demande_avenant_rejeter(request, pk):
    demande = get_object_or_404(DemandeAvenant, pk=pk)
    refus = verifier_acces_gestion_contrat(request.user, demande.contrat_commercial)
    if refus:
        return refus
    ...
```

**GET** :
- Si `demande.statut != 'EN_ATTENTE'` : même message qu'en 1.1, pas de
  formulaire.
- Sinon : formulaire à un seul champ, `commentaire_validation` (motif),
  **obligatoire** (arbitrage n°3). Contrairement à la validation, le
  rejet **n'est pas bloqué** si le contrat n'est plus `ACTIF` — tranché
  explicitement (arbitrage complémentaire du 24/09/2026) : la validation
  produit un effet sur le périmètre, donc exige un contrat `ACTIF` ; le
  rejet ne modifie ni le contrat ni le périmètre, il acte seulement une
  décision administrative de clôture. Permet notamment de rejeter
  explicitement, avec motif (« Demande devenue obsolète suite au
  renouvellement du contrat »), une demande restée liée à un contrat
  devenu `EXPIRE`/`RESILIE` plutôt que de la laisser indéfiniment
  `EN_ATTENTE`.

**POST** :

```python
    from django.db import transaction
    with transaction.atomic():
        demande = get_object_or_404(
            DemandeAvenant.objects.select_for_update(), pk=pk
        )
        if demande.statut != 'EN_ATTENTE':
            messages.error(request, "Cette demande a déjà été traitée.")
            return redirect('registre:demande_avenant_liste')

        form = DemandeAvenantRejetForm(request.POST, instance=demande)
        if not form.is_valid():
            return render(request, 'registre/commercial/demande_avenant_rejeter.html', {
                'demande': demande, 'form': form,
            })

        demande = form.save(commit=False)
        demande.statut = 'REJETEE'
        demande.validateur = request.user
        demande.date_traitement = timezone.now()
        demande.save()

    messages.success(request, "Demande rejetée.")
    return redirect('registre:demande_avenant_liste')
```

**Verrou** : seule la `DemandeAvenant` est verrouillée
(`select_for_update()`) — jamais le `ContratCommercial`. Tranché
explicitement (arbitrage complémentaire du 24/09/2026) : le rejet
n'écrit jamais sur le contrat ni sur le périmètre, verrouiller le
contrat n'apporterait donc aucune garantie fonctionnelle supplémentaire
et élargirait inutilement la portée de la transaction. Le risque que
l'arbitrage n°5 vise (valider contre un état contractuel qui vient de
changer) est propre à la validation, pas au rejet.

---

## 2. Formulaires

Un seul nouveau formulaire, `registre/forms.py` :

```python
class DemandeAvenantRejetForm(forms.ModelForm):
    class Meta:
        model = DemandeAvenant
        fields = ['commentaire_validation']
        widgets = {
            'commentaire_validation': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 4,
                'placeholder': "Motif du rejet (obligatoire)",
            }),
        }
        labels = {'commentaire_validation': 'Motif du rejet'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obligatoire uniquement pour le rejet — le champ reste
        # blank=True au niveau du modèle (arbitrage DT n°3, DECISIONS.md).
        self.fields['commentaire_validation'].required = True
```

Rien côté validation (`demande_avenant_valider`) : aucune saisie
utilisateur, uniquement une confirmation (comme `activer_contrat`, qui
n'a pas de formulaire non plus).

---

## 3. Routes

```python
# Contractualisation — validation/rejet des demandes d'avenant
# (P5-L1, Lot C4).
path('commercial/demandes/<int:pk>/valider/', views.demande_avenant_valider, name='demande_avenant_valider'),
path('commercial/demandes/<int:pk>/rejeter/', views.demande_avenant_rejeter, name='demande_avenant_rejeter'),
```

Même famille que les routes C2/C3 déjà en place sous `commercial/`.

---

## 4. Templates

Deux nouveaux templates, `Templates/registre/commercial/` :

- **`demande_avenant_valider.html`** — reprend le style de
  `activer_contrat.html` (`.effet-box`, `.refus-box`) : bloc d'erreur si
  demande déjà traitée ou contrat non `ACTIF` (pas de bouton) ; sinon,
  liste des effets (AJOUT en bleu, RETRAIT en orange — mêmes classes que
  `demande_avenant_form.html` côté confirmation C3), impact tarifaire,
  bandeau d'avertissement si date dépassée, formulaire POST à un seul
  bouton `[Confirmer la validation]`.
- **`demande_avenant_rejeter.html`** — reprend le style de
  `resiliation_form.html` : formulaire avec le champ motif (obligatoire,
  erreur affichée si vide), bouton `[Confirmer le rejet]`.

**Modification de `demande_avenant_liste.html`** (existant, C3) : ajout,
pour chaque ligne `EN_ATTENTE` dont l'utilisateur peut gérer le contrat
(`gestion_contrat_autorisee(request.user, demande.contrat_commercial)`,
calculé par ligne dans la vue), de deux liens `Valider`/`Rejeter` — sauf
si la demande est déjà signalée non validable (contrat non `ACTIF`), où
seul `Rejeter` reste proposé (cohérent avec 1.2 : le rejet reste
possible, pas la validation). Nécessite de passer au template, par
demande, un indicateur `peut_traiter` calculé dans `demande_avenant_liste`
(vue existante, C3) — seule modification requise à cette vue.

---

## 5. Transaction et verrouillage

Déjà détaillé en §1.1/§1.2. Résumé :

| Vue | Verrous | Revérifié après verrou |
|---|---|---|
| `demande_avenant_valider` | `DemandeAvenant` + `ContratCommercial` | `demande.statut == 'EN_ATTENTE'` et `contrat.statut == 'ACTIF'` |
| `demande_avenant_rejeter` | `DemandeAvenant` seule | `demande.statut == 'EN_ATTENTE'` |

Limitation SQLite déjà connue et acceptée (Lot C2) : `select_for_update()`
est un no-op silencieux sur SQLite (moteur de production actuel) —
aucune protection réelle contre la concurrence tant que PSM2S reste sur
ce moteur. Le code et les tests sont écrits comme si la protection était
réelle (pour être prêts sans modification si le moteur change un jour),
avec un test dédié qui `skipTest()` explicitement sur SQLite plutôt que
de simuler une fausse couverture — même patron que
`ActiverContratTests.test_select_for_update_utilise_dans_la_transaction`.

---

## 6. Génération des `MouvementPerimetre` (AJOUT/RETRAIT)

Un `MouvementPerimetre` par `LigneDemandeAvenant` de la demande, dans la
boucle du §1.1 — `type_mouvement`/`type_objet`/`etablissement`/
`batiment` copiés tels quels depuis la ligne, `date_effet` =
`demande.date_effet_souhaitee`, `ligne_demande_origine` = la ligne
elle-même. `etablissement_code_historique`/`nom_historique` ne sont
jamais passés explicitement — `MouvementPerimetre.save()` les déduit
automatiquement de l'objet lié quand ils sont absents (comportement déjà
existant, vérifié dans `models.py`, réutilisé sans modification).

Aucune distinction de traitement entre AJOUT et RETRAIT à ce niveau : la
boucle est strictement mécanique, la nature du mouvement est déjà
entièrement déterminée par `ligne.type_mouvement` au moment de la
soumission (C3) — C4 ne réinterprète jamais une ligne, il la transforme
telle quelle en mouvement appliqué.

---

## 7. Impossibilité de double validation

Garantie par la combinaison de trois éléments, aucun nouveau mécanisme :
1. **Contrôle anti-doublon de C3** (déjà en place, inchangé) : au plus
   une `DemandeAvenant` `EN_ATTENTE` peut toucher un établissement/
   bâtiment donné sur un même contrat — deux demandes distinctes ne
   peuvent jamais entrer en conflit à la validation.
2. **Contrôle de statut après verrou** (§1.1/§5) : une fois la demande
   passée à `VALIDEE` dans la transaction, toute tentative concurrente
   qui obtiendrait le verrou ensuite trouve `statut != 'EN_ATTENTE'` et
   s'arrête sans écriture.
3. **`select_for_update()` sur la `DemandeAvenant`** (§5) : ferme la
   fenêtre de course entre la lecture du statut et son écriture — sans
   ce verrou, deux transactions concurrentes pourraient toutes deux lire
   `EN_ATTENTE` avant que l'une des deux n'écrive `VALIDEE`. Sur SQLite
   (limitation connue, §5), cette protection n'est pas réelle en
   production actuellement — seul le test dédié en documente l'intention
   pour un futur changement de moteur.

---

## 8. Conservation de la demande et des mouvements comme historique

Aucune suppression, jamais. Une `DemandeAvenant` `REJETEE` reste visible
dans `demande_avenant_liste` (déjà le cas depuis C3, aucun filtre par
statut n'existe dans cette vue). Les `MouvementPerimetre` produits par
une validation ne sont jamais modifiés ni supprimés par ce lot — aucune
vue de C4 ne touche un `MouvementPerimetre` existant, uniquement
`DemandeAvenant.objects.create(...)` en écriture nouvelle. Le lien
`ligne.mouvement` (déjà exploité par `demande_avenant_liste.html` depuis
C3) continue de fonctionner sans changement pour toute demande validée
par C4.

---

## 9. Comportement des demandes dont le contrat est devenu non `ACTIF`

Détaillé en §1.1 (validation) et §1.2 (rejet). Résumé de l'arbitrage
n°2 : **jamais de rejet automatique**. Une demande `EN_ATTENTE` dont le
contrat a cessé d'être `ACTIF` (renouvelé via C2, ou résilié) reste
`EN_ATTENTE` indéfiniment tant que personne n'agit explicitement dessus
— seule une action humaine explicite (rejet manuel, motif obligatoire)
peut la faire sortir de cet état ; la validation lui reste fermée tant
que le contrat n'est pas de nouveau `ACTIF` (ce qui, par construction du
modèle — un seul contrat `ACTIF` à la fois, jamais réactivé — n'arrivera
en pratique jamais pour un `ContratCommercial` donné une fois qu'il a
quitté ce statut). En pratique, une demande bloquée de cette façon ne
sortira donc de `EN_ATTENTE` que par un rejet manuel — signalé comme
conséquence logique de l'arbitrage n°2, pas comme un défaut.

---

## 10. Avertissement sur `date_effet_souhaitee` passée

Détaillé en §1.1. Purement un affichage côté vue GET (`demande.
date_effet_souhaitee < timezone.now().date()`) — aucune conséquence sur
le comportement du POST, qui procède normalement. Aucun champ ni
mécanisme de confirmation séparé introduit : le bouton de confirmation
déjà présent sur l'écran vaut confirmation, conformément à l'arbitrage
n°4 (« avertissement, pas blocage »).

---

## 11. Permissions et contrôles IDOR

- **Décorateur** : `@gestionnaire_requis` (admin/responsable_securite/
  directeur) sur les deux vues, identique à `resiliation_form`.
- **Contrôle par objet** : `verifier_acces_gestion_contrat(request.user,
  demande.contrat_commercial)` — refus par **redirection** vers le
  dashboard (arbitrage n°6), jamais `Http404`. Un directeur non
  gestionnaire du contrat, ou gestionnaire d'un **autre** contrat, est
  refusé de la même façon qu'un `resiliation_form` sur un contrat qu'il
  ne gère pas — aucune fonction nouvelle, réutilisation stricte du Lot
  B.
- **IDOR via `pk`** : le `pk` de la route est celui de la
  `DemandeAvenant`, pas du contrat — `get_object_or_404(DemandeAvenant,
  pk=pk)` peut lever `Http404` si l'identifiant n'existe pas du tout
  (comportement Django standard, pas une fuite d'information
  spécifique : identique pour n'importe quel objet inexistant dans
  PSM2S), puis `verifier_acces_gestion_contrat` prend le relais pour le
  cas où l'objet existe mais appartient à un contrat non géré par
  l'utilisateur.

---

## 12. Vérification — aucune décision C0-C3 implicitement modifiée

Relecture explicite avant de clore cette proposition :
- **C0** (`perimetre_a_date`, `tarif_mensuel`, `statut_coherent`) :
  aucune modification — C4 les appelle telles quelles pour le
  récapitulatif de validation (§1.1), comme C1/C3 le font déjà.
- **C1** (consultation) : aucune vue C1 touchée. La restriction
  d'affichage des agrégats à `peut_voir_agregats` reste inchangée — la
  visibilité intégrale des montants sur l'écran de validation (§1.1)
  n'est pas une exception à cette règle, puisque atteindre cet écran
  suppose déjà `gestion_contrat_autorisee` (même condition qui donne
  `peut_voir_agregats=True` sur `contrat_detail`).
- **C2** (`renouvellement_form`, `activer_contrat`, `resiliation_form`) :
  aucune modification. La règle « un seul contrat `ACTIF` à la fois »
  et la séquence EXPIRE-avant-ACTIF restent strictement du ressort de
  `activer_contrat` — C4 ne modifie jamais `ContratCommercial.statut`,
  seulement `DemandeAvenant.statut` et la création de
  `MouvementPerimetre`.
- **C3** (`demande_avenant_form`, `demande_avenant_liste`,
  `demandes_avenant_visibles`) : `demande_avenant_form` non touchée —
  C4 ne modifie ni la structure des `LigneDemandeAvenant` produites ni
  le contrôle anti-doublon. `demande_avenant_liste` reçoit uniquement
  l'ajout de l'indicateur `peut_traiter` par ligne (§4) et des liens
  d'action — aucune modification du queryset ni de la logique de
  visibilité (`demandes_avenant_visibles`, Lot B, non touchée).
- **Modèles (Lot A)** : aucun champ ajouté, aucune migration.

---

## 13. Tests à écrire

- **Autorisation** (les deux vues) : admin/responsable_securite/
  gestionnaire du contrat autorisés ; directeur non gestionnaire refusé ;
  gestionnaire d'un autre contrat refusé ; factotum/prestataire refusés
  — toutes par redirection vers `registre:dashboard`.
- **IDOR** : `pk` d'une demande dont l'utilisateur ne gère pas le
  contrat → redirection, aucune écriture.
- **Validation nominale** : demande `EN_ATTENTE` sur contrat `ACTIF` →
  statut `VALIDEE`, `validateur`/`date_traitement` renseignés, un
  `MouvementPerimetre` par `LigneDemandeAvenant` (AJOUT et RETRAIT dans
  le même test), `date_effet` correcte, `ligne_demande_origine` correct.
- **Rejet nominal** : demande `EN_ATTENTE`, motif renseigné → statut
  `REJETEE`, `commentaire_validation` enregistré, aucun
  `MouvementPerimetre` créé, `perimetre_a_date` inchangé.
- **Rejet sans motif** : formulaire invalide, aucune écriture, demande
  reste `EN_ATTENTE`.
- **Demande déjà traitée** : tentative de validation et de rejet sur une
  demande déjà `VALIDEE`/`REJETEE` → refus propre, aucune écriture,
  aucun nouveau `MouvementPerimetre`, aucune modification des
  `MouvementPerimetre` déjà existants.
- **Contrat non `ACTIF`** : tentative de validation → refus, aucune
  écriture, `demande.statut` reste `EN_ATTENTE` (jamais `REJETEE`).
  Tentative de rejet sur le même cas → autorisée (§1.2), produit bien
  `REJETEE` avec le motif fourni.
- **Cas du renouvellement** : demande restée liée à l'ancien contrat
  après un `activer_contrat` (C2) → même comportement que « contrat non
  `ACTIF` » ci-dessus, aucun transfert vers le nouveau contrat.
- **Avertissement date passée** : `date_effet_souhaitee` antérieure à
  aujourd'hui → contexte GET signale l'avertissement ; la validation
  aboutit normalement si confirmée (aucun blocage).
- **Atomicité/rollback** : même patron que
  `ActiverContratTests.test_rollback_complet_si_echec_en_cours_de_transaction`
  — simuler un échec après l'écriture du statut `VALIDEE` mais avant la
  fin de la création des `MouvementPerimetre` (ex. `patch` sur
  `MouvementPerimetre.save` qui échoue à la seconde ligne d'une demande
  à trois lignes) : la demande doit rester `EN_ATTENTE`, aucun
  `MouvementPerimetre` ne doit persister.
- **Concurrence/verrouillage** : vérifier la présence effective de
  `select_for_update()` sur `DemandeAvenant` (les deux vues) et sur
  `ContratCommercial` (validation uniquement) — `skipTest()` sur SQLite,
  même patron que C2.
- **Historique** : `ligne.mouvement` accessible après validation (déjà
  couvert côté template par C3, à revérifier après ajout des nouvelles
  vues) ; une demande `REJETEE` reste visible dans
  `demande_avenant_liste`.

---

## 14. Arbitrages — état final

Les deux points laissés ouverts par la première version de cette
proposition sont désormais tranchés (arbitrages complémentaires du
24/09/2026, `DECISIONS.md`) :

1. **Rejet d'une demande dont le contrat n'est plus `ACTIF`** : reste
   possible, sans restriction (§1.2, §9, §13).
2. **Portée du double verrouillage** : uniquement pour la validation
   (`DemandeAvenant` + `ContratCommercial`) ; le rejet ne verrouille que
   `DemandeAvenant` (§1.2, §5).

Aucun autre point de cette proposition ne s'écarte des six arbitrages du
24/09/2026, des deux arbitrages complémentaires, ni des décisions déjà
actées en C0-C3 (§12). **Aucun point bloquant restant** avant
développement, sous réserve de la validation finale du DT.
