# ─────────────────────────────────────────────
#  AUDIT (lecture seule) des donnees demo PSM2S sur formation
#  Aucune ecriture en base — uniquement des requetes de lecture.
#
#  Execution, sur formation, en SSH (venv active) :
#    DJANGO_SETTINGS_MODULE=config.settings_formation python manage.py shell < audit_donnees_demo.py
# ─────────────────────────────────────────────

from registre.models import (
    Etablissement, Batiment, Utilisateur, EtablissementUtilisateur,
    ControleEtablissement, RealisationControle,
    Prestataire, Contrat, CorrespondantLocal,
    TicketTravaux, Intervention, PieceJointeTicket,
    VisiteCommission, Prescription, ActionPrescription,
    DUERP, DroitSignature, Document,
)

L = "=" * 70

def titre(t):
    print("\n" + L)
    print(t)
    print(L)

# ── 1. Vue d'ensemble : tous les etablissements presents ────────────
titre("TOUS LES ETABLISSEMENTS EN BASE")
for e in Etablissement.objects.all().order_by('nom'):
    print(f"- [{e.code}] {e.nom} | ville={e.ville or '—'} | type_erp={e.type_erp or '—'} | categorie={e.categorie or '—'} | actif={e.actif}")

# ── 2. Detail des 3 etablissements demo ──────────────────────────────
codes_demo = ['DEMO-TIL', 'DEMO-CER', 'DEMO-VAL']
etabs = {e.code: e for e in Etablissement.objects.filter(code__in=codes_demo)}

for code in codes_demo:
    etab = etabs.get(code)
    if not etab:
        titre(f"{code} — INTROUVABLE EN BASE")
        continue

    titre(f"ETABLISSEMENT : {etab.nom} ({etab.code})")
    print(f"Ville: {etab.ville or '—'} | Contact sur place: {etab.contact_nom or '—'} ({etab.contact_telephone or '—'}, {etab.contact_email or '—'})")

    print("\n-- Batiments --")
    for b in etab.batiments.all():
        print(f"  - {b.nom} | capacite={b.capacite_accueil or '—'} | actif={b.actif}")

    print("\n-- Utilisateurs rattaches --")
    for eu in EtablissementUtilisateur.objects.filter(etablissement=etab).select_related('utilisateur'):
        u = eu.utilisateur
        niveau = f" (niveau {u.niveau_factotum})" if u.role == 'factotum' else ""
        print(f"  - {u.get_full_name() or u.username} | role={u.get_role_display()}{niveau} | username={u.username} | principal={eu.principal}")

    print("\n-- Controles reglementaires --")
    controles = ControleEtablissement.objects.filter(etablissement=etab).select_related('type_controle', 'batiment')
    for c in controles:
        print(f"  - [{c.type_controle.categorie}] {c.type_controle.nom} | statut={c.get_statut_display()} | priorite={c.get_priorite_display()} | realise={c.date_realisation or '—'} | echeance={c.prochaine_echeance or '—'} | batiment={c.batiment.nom if c.batiment else '—'}")
    print(f"  Total : {controles.count()} controle(s)")

    print("\n-- Realisations (historique) --")
    realisations = RealisationControle.objects.filter(controle__etablissement=etab)
    for r in realisations:
        print(f"  - {r.controle.type_controle.nom} | annee={r.annee} | date={r.date_realisation} | organisme={r.organisme or '—'}")
    print(f"  Total : {realisations.count()} realisation(s)")

    print("\n-- Contrats prestataires --")
    contrats = Contrat.objects.filter(etablissement=etab).select_related('prestataire_fk', 'type_controle')
    for c in contrats:
        prest = c.prestataire_fk.nom if c.prestataire_fk else '—'
        print(f"  - {prest} | type_controle={c.type_controle.nom if c.type_controle else '—'} | numero={c.numero or '—'} | debut={c.date_debut or '—'} | fin={c.date_fin or '—'} | montant={c.montant or '—'} | expire_bientot={c.expire_bientot}")
    print(f"  Total : {contrats.count()} contrat(s)")

    print("\n-- Correspondants locaux (prestataires) --")
    correspondants = CorrespondantLocal.objects.filter(etablissement=etab).select_related('prestataire')
    for co in correspondants:
        print(f"  - {co.prestataire.nom} -> {co.nom or '(sans nom)'} | tel={co.telephone or '—'} | email={co.email or '—'} | notes={co.notes[:50] if co.notes else '—'}")
    print(f"  Total : {correspondants.count()} correspondant(s)")

    print("\n-- Tickets travaux --")
    tickets = TicketTravaux.objects.filter(etablissement=etab).select_related('responsable')
    for t in tickets:
        resp = t.responsable.get_full_name() if t.responsable else '—'
        print(f"  - \"{t.titre}\" | statut={t.get_statut_display()} | priorite={t.get_priorite_display()} | responsable={resp} | cout_estime={t.cout_estime or '—'} | cout_reel={t.cout_reel or '—'}")
        pieces = PieceJointeTicket.objects.filter(ticket=t)
        for pj in pieces:
            print(f"      piece jointe: {pj.nom_fichier} ({pj.get_type_piece_display()})")
        interventions = Intervention.objects.filter(ticket=t)
        for i in interventions:
            print(f"      intervention: {i.prestataire or 'interne'} | {i.date_intervention} | statut={i.get_statut_display()} | montant={i.montant or '—'}")
    print(f"  Total : {tickets.count()} ticket(s)")

    print("\n-- Visites de commission --")
    visites = VisiteCommission.objects.filter(etablissement=etab)
    for v in visites:
        prescriptions = Prescription.objects.filter(visite=v)
        print(f"  - Visite du {v.date_visite} | PV recu le {v.date_pv or '—'} | {prescriptions.count()} prescription(s)")
        for p in prescriptions:
            actions = ActionPrescription.objects.filter(prescription=p).count()
            print(f"      prescription #{p.numero or '—'} | statut={p.get_statut_display()} | delai={p.delai or '—'} | {actions} action(s) de suivi")
    print(f"  Total : {visites.count()} visite(s)")

    print("\n-- DUERP --")
    duerps = DUERP.objects.filter(etablissement=etab)
    for d in duerps:
        print(f"  - Annee {d.annee} | statut={d.get_statut_display()} | signe_directeur={'oui - ' + d.nom_directeur if d.signature_directeur else 'non'} | signe_responsable={'oui - ' + d.nom_responsable if d.signature_responsable else 'non'}")
        droits = DroitSignature.objects.filter(etablissement=etab, document='duerp')
        for dr in droits:
            print(f"      droit de signature DUERP: {dr.utilisateur.get_full_name() or dr.utilisateur.username}")
    print(f"  Total : {duerps.count()} DUERP")

    print("\n-- Documents (rapports/PV/attestations sur controles) --")
    documents = Document.objects.filter(controle__etablissement=etab)
    for doc in documents:
        print(f"  - {doc.nom_fichier} | type={doc.get_type_doc_display()} | controle={doc.controle.type_controle.nom}")
    print(f"  Total : {documents.count()} document(s)")

# ── 3. Referentiel prestataires global (pas limite aux 3 etabs) ─────
titre("REFERENTIEL PRESTATAIRES (global)")
for p in Prestataire.objects.all().order_by('nom'):
    nb_contrats = Contrat.objects.filter(prestataire_fk=p).count()
    nb_correspondants = CorrespondantLocal.objects.filter(prestataire=p).count()
    print(f"- {p.nom} | contact={p.contact_nom or '—'} | tel={p.telephone or '—'} | email={p.email or '—'} | {nb_contrats} contrat(s) | {nb_correspondants} correspondant(s) local(aux)")

titre("FIN DE L'AUDIT")
