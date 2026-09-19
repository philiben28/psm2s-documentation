# ─────────────────────────────────────────────
#  CORRECTION des donnees demo PSM2S (Tilleuls / Cerisiers / Vallon Fleuri)
#
#  NE TOUCHE QUE les enregistrements lies aux codes DEMO-TIL, DEMO-CER,
#  DEMO-VAL. Aucune reference aux 5 autres etablissements presents en
#  base (FVH, IME-Tremplin, MAS-Fontaines, EHPAD, SESSAD) — hors
#  perimetre, non touches, meme indirectement.
#
#  A executer le jour meme (ou la veille) du tournage, pas avant :
#  les echeances sont calculees par rapport a la date du jour au
#  moment de l'execution.
#
#  Execution, sur formation, en SSH (venv active) :
#    DJANGO_SETTINGS_MODULE=config.settings_formation python manage.py shell < correction_donnees_demo.py
# ─────────────────────────────────────────────

import datetime
from registre.models import (
    Etablissement, Utilisateur, ControleEtablissement,
    VisiteCommission, Intervention, TicketTravaux,
)

today = datetime.date.today()
jours = datetime.timedelta

def j(n):
    return today + jours(days=n)

etab_tilleuls = Etablissement.objects.get(code='DEMO-TIL')

print(f"Date du jour utilisee pour le recalcul : {today}")

# ── 1. Supprimer la visite de commission en double (garder la plus recente) ──
visite_a_supprimer = VisiteCommission.objects.filter(
    etablissement=etab_tilleuls, date_visite=datetime.date(2026, 5, 18)
).first()
if visite_a_supprimer:
    nb_presc = visite_a_supprimer.prescriptions.count()
    visite_a_supprimer.delete()  # cascade : prescriptions + actions de suivi
    print(f"Visite du 2026-05-18 supprimee (avec {nb_presc} prescription(s) liee(s)).")
else:
    print("Visite du 2026-05-18 introuvable (deja supprimee ou jamais creee) — rien fait.")

visite_conservee = VisiteCommission.objects.filter(
    etablissement=etab_tilleuls, date_visite=datetime.date(2026, 5, 21)
).first()
print(f"Visite conservee : {visite_conservee}" if visite_conservee else "ATTENTION : visite du 2026-05-21 introuvable !")

# ── 2. Supprimer l'intervention en double sur le ticket extincteur ──────────
ticket_extincteur = TicketTravaux.objects.filter(
    etablissement=etab_tilleuls, titre="Remplacement extincteur hall d'entrée"
).first()
if ticket_extincteur:
    intervention_a_supprimer = Intervention.objects.filter(
        ticket=ticket_extincteur, date_intervention=datetime.date(2026, 7, 24)
    ).first()
    if intervention_a_supprimer:
        intervention_a_supprimer.delete()
        print("Intervention du 2026-07-24 supprimee (doublon).")
    else:
        print("Intervention du 2026-07-24 introuvable — rien fait.")
else:
    print("Ticket 'Remplacement extincteur hall d'entrée' introuvable — verifie le titre exact.")

# ── 3. Ascenseur Tilleuls -> EN RETARD ───────────────────────────────────────
ctrl_ascenseur = ControleEtablissement.objects.filter(
    etablissement=etab_tilleuls, type_controle__categorie='ascenseur'
).first()
if ctrl_ascenseur:
    ancienne = ctrl_ascenseur.prochaine_echeance
    ctrl_ascenseur.prochaine_echeance = j(-12)
    ctrl_ascenseur.save()
    print(f"Ascenseur : echeance {ancienne} -> {ctrl_ascenseur.prochaine_echeance} (en retard)")
else:
    print("Controle ascenseur introuvable sur Tilleuls — rien fait.")

# ── 4. Alarme incendie Tilleuls -> ECHEANCE PROCHE ──────────────────────────
ctrl_incendie = ControleEtablissement.objects.filter(
    etablissement=etab_tilleuls, type_controle__nom='Alarme incendie'
).first()
if ctrl_incendie:
    avant = (ctrl_incendie.statut, ctrl_incendie.priorite, ctrl_incendie.prochaine_echeance)
    ctrl_incendie.statut = 'a_remettre_a_jour'
    ctrl_incendie.priorite = 'urgent'
    ctrl_incendie.prochaine_echeance = j(8)
    ctrl_incendie.save()
    print(f"Alarme incendie : {avant} -> ({ctrl_incendie.statut}, {ctrl_incendie.priorite}, {ctrl_incendie.prochaine_echeance})")
else:
    print("Controle 'Alarme incendie' introuvable sur Tilleuls — rien fait.")

# ── 5. Controle DUERP (type reglementaire) Tilleuls -> A VENIR ─────────────
ctrl_duerp = ControleEtablissement.objects.filter(
    etablissement=etab_tilleuls, type_controle__nom='DUERP'
).first()
if ctrl_duerp:
    avant = (ctrl_duerp.priorite, ctrl_duerp.prochaine_echeance)
    ctrl_duerp.priorite = 'normal'
    ctrl_duerp.prochaine_echeance = j(55)
    ctrl_duerp.save()
    print(f"Controle DUERP : {avant} -> ({ctrl_duerp.priorite}, {ctrl_duerp.prochaine_echeance})")
else:
    print("Controle type 'DUERP' introuvable sur Tilleuls — rien fait.")

# ── 6. Niveau de Karim (factotum) : 2 -> 3 ──────────────────────────────────
karim = Utilisateur.objects.filter(username='demo_factotum').first()
if karim:
    avant = karim.niveau_factotum
    karim.niveau_factotum = 3
    karim.save()
    print(f"Karim Belhadj : niveau_factotum {avant} -> {karim.niveau_factotum}")
else:
    print("Compte demo_factotum introuvable — rien fait.")

# ── 7. Responsable du ticket ascenseur -> Karim ─────────────────────────────
ticket_ascenseur = TicketTravaux.objects.filter(
    etablissement=etab_tilleuls, titre="Remise en service ascenseur bâtiment principal"
).first()
if ticket_ascenseur and karim:
    ticket_ascenseur.responsable = karim
    ticket_ascenseur.save()
    print(f"Ticket ascenseur : responsable -> {karim.get_full_name()}")
else:
    print("Ticket ascenseur ou compte Karim introuvable — rien fait.")

print("\nCorrection terminee. Aucun etablissement hors DEMO-TIL/CER/VAL n'a ete touche.")
