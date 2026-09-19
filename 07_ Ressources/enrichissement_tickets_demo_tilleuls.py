# ─────────────────────────────────────────────
#  ENRICHISSEMENT TICKETS DEMO — IME Les Tilleuls (DEMO-TIL)
#  10 cas de maintenance/vie quotidienne du batiment.
#
#  Remplace extension_quotidien_tilleuls.py (jamais execute) : les cas 1 a 4
#  sont identiques a ce script precedent, desormais obsolete au profit de
#  celui-ci qui couvre les 10 cas valides le 03/09/2026.
#
#  Idempotent : cle de lookup stable = titre du ticket (jamais de date
#  relative dans une cle get_or_create). Les dates relatives ne sont mises
#  que dans les 'defaults' / mises a jour ciblees.
#
#  NE TOUCHE QUE DEMO-TIL. Ne cree, ne modifie et ne supprime :
#   - aucun compte, role ou permission utilisateur
#   - aucun controle reglementaire
#   - aucun des 3 tickets deja existants (registre securite, ascenseur,
#     extincteur) : les cles get_or_create ci-dessous portent sur des
#     titres totalement distincts, verifie par l'inspection du 03/09/2026.
#
#  Execution, sur formation, en SSH (venv active) :
#    DJANGO_SETTINGS_MODULE=config.settings_formation python manage.py shell < enrichissement_tickets_demo_tilleuls.py
# ─────────────────────────────────────────────

import datetime
from django.utils import timezone
from registre.models import (
    Etablissement, Utilisateur, Prestataire, CorrespondantLocal,
    TicketTravaux, Intervention,
)

today = datetime.date.today()
jours = datetime.timedelta


def j(n):
    return today + jours(days=n)


def dt(n, heure=10):
    """Datetime timezone-aware, n jours par rapport a aujourd'hui."""
    naive = datetime.datetime.combine(j(n), datetime.time(heure, 0))
    return timezone.make_aware(naive)


etab = Etablissement.objects.get(code='DEMO-TIL')
nathalie = Utilisateur.objects.get(username='demo_directeur')
karim = Utilisateur.objects.get(username='demo_factotum')

# ── Prestataire du quotidien : AMEB Multiservices ───────────────────────────
ameb = Prestataire.objects.get_or_create_normalise('AMEB Multiservices')
if not ameb.contact_nom:
    ameb.contact_nom = "Yannick Ferreira"
    ameb.telephone = "02 00 00 20 20"
    ameb.email = "contact@ameb-multiservices.fr"
    ameb.adresse = "Zone artisanale, Clairvallon"
    ameb.save()

CorrespondantLocal.objects.get_or_create(
    prestataire=ameb, etablissement=etab,
    defaults=dict(
        nom="Yannick Ferreira", telephone="06 00 00 21 22",
        email="y.ferreira@ameb-multiservices.fr",
        notes="Intervient sous 48h en général, prévenir l'accueil avant son passage.",
    )
)


def creer_ticket(titre, description, priorite, statut, cree_par,
                  jour_creation, cout_estime=None, cout_reel=None,
                  jour_cloture=None):
    t, _ = TicketTravaux.objects.get_or_create(
        etablissement=etab, titre=titre,
        defaults=dict(
            description=description, priorite=priorite, statut=statut,
            responsable=karim, cree_par=cree_par,
            date_cible=j(jour_creation + 5),
            cout_estime=cout_estime, cout_reel=cout_reel,
            date_cloture=dt(jour_cloture, 16) if jour_cloture is not None else None,
        )
    )
    # date_creation est en auto_now_add : get_or_create() l'ignore au moment
    # de la creation, on la fixe donc explicitement apres coup.
    TicketTravaux.objects.filter(pk=t.pk).update(date_creation=dt(jour_creation, 9))
    return t


def creer_intervention(ticket, jour, description, statut, interne=False,
                        prestataire='', montant=None):
    i, _ = Intervention.objects.get_or_create(
        ticket=ticket,
        defaults=dict(
            realise_en_interne=interne, prestataire=prestataire,
            date_intervention=j(jour), description=description,
            statut=statut, montant=montant, saisie_par=karim,
        )
    )
    Intervention.objects.filter(pk=i.pk).update(date_creation=dt(jour, 11))
    return i


# ── Cas 1 : fontaines a eau (interne, cloture) ──────────────────────────────
t1 = creer_ticket(
    "Réapprovisionnement consommables fontaines à eau",
    "Stock de gobelets et filtres des fontaines à eau du bâtiment principal "
    "presque épuisé, à renouveler avant rupture.",
    priorite='faible', statut='cloture', cree_par=karim,
    jour_creation=-35, cout_estime=40, cout_reel=35, jour_cloture=-33,
)
creer_intervention(t1, jour=-34, interne=True, statut='realisee', montant=35,
                    description="Réapprovisionnement effectué directement auprès du fournisseur habituel.")

# ── Cas 2 : bande podotactile (interne, urgent, cloture) ───────────────────
t2 = creer_ticket(
    "Bande podotactile décollée — escalier principal",
    "Bande de vigilance podotactile partiellement décollée en haut de "
    "l'escalier principal, risque de chute.",
    priorite='urgent', statut='cloture', cree_par=nathalie,
    jour_creation=-30, cout_estime=15, cout_reel=12, jour_cloture=-29,
)
creer_intervention(t2, jour=-29, interne=True, statut='realisee', montant=12,
                    description="Recollage de la bande avec colle spécifique, vérification de l'adhérence.")

# ── Cas 3 : eclairage (externe AMEB, cloture) ───────────────────────────────
t3 = creer_ticket(
    "Éclairage défaillant — couloir bâtiment principal",
    "Plusieurs points lumineux hors service dans le couloir menant aux "
    "chambres, ballast probablement à remplacer.",
    priorite='normal', statut='cloture', cree_par=karim,
    jour_creation=-24, cout_estime=110, cout_reel=95, jour_cloture=-21,
)
creer_intervention(t3, jour=-21, prestataire='AMEB Multiservices', statut='realisee', montant=95,
                    description="Remplacement de 2 ballasts électroniques et d'un tube néon.")

# ── Cas 4 : fuite sanitaire (externe AMEB, EN COURS) ────────────────────────
t4 = creer_ticket(
    "Fuite sanitaire — lavabo rez-de-chaussée",
    "Fuite au niveau du mitigeur d'un lavabo, sanitaire du rez-de-chaussée.",
    priorite='urgent', statut='en_cours', cree_par=nathalie,
    jour_creation=-4, cout_estime=55,
)
creer_intervention(t4, jour=2, prestataire='AMEB Multiservices', statut='planifiee',
                    description="Devis reçu, intervention planifiée pour remplacement du mitigeur.")

# ── Cas 5 : porte coupe-feu (externe AMEB, EN COURS) ────────────────────────
t5 = creer_ticket(
    "Porte difficile à fermer — bâtiment principal",
    "Une porte coupe-feu du bâtiment principal ferme mal, réglage des "
    "charnières ou du ferme-porte à vérifier.",
    priorite='normal', statut='en_cours', cree_par=nathalie,
    jour_creation=-9, cout_estime=60,
)
creer_intervention(t5, jour=3, prestataire='AMEB Multiservices', statut='planifiee',
                    description="Visite programmée pour réglage/vérification de la porte coupe-feu.")

# ── Cas 6 : robinet qui goutte (interne, cloture) ───────────────────────────
t6 = creer_ticket(
    "Robinet qui goutte — local de service",
    "Léger goutte-à-goutte constaté sur un robinet du local de service.",
    priorite='faible', statut='cloture', cree_par=karim,
    jour_creation=-18, cout_estime=10, cout_reel=8, jour_cloture=-17,
)
creer_intervention(t6, jour=-17, interne=True, statut='realisee', montant=8,
                    description="Resserrage et changement d'un joint.")

# ── Cas 7 : stock produits d'entretien (a traiter, sans intervention) ──────
t7 = creer_ticket(
    "Réapprovisionnement produits d'entretien",
    "Plusieurs produits d'entretien courants arrivent à un niveau faible, "
    "commande à prévoir.",
    priorite='normal', statut='a_traiter', cree_par=karim,
    jour_creation=-7, cout_estime=30,
)
# Pas d'intervention : rien n'a encore ete fait, coherent avec "a traiter".

# ── Cas 8 : radiateur (externe AMEB, cloture) ───────────────────────────────
t8 = creer_ticket(
    "Radiateur insuffisamment chauffant — salle d'activité",
    "Un radiateur chauffe insuffisamment dans une salle d'activité.",
    priorite='normal', statut='cloture', cree_par=nathalie,
    jour_creation=-14, cout_estime=80, cout_reel=75, jour_cloture=-12,
)
creer_intervention(t8, jour=-12, prestataire='AMEB Multiservices', statut='realisee', montant=75,
                    description="Purge et équilibrage du circuit, vanne thermostatique remplacée.")

# ── Cas 9 : poignee de porte (interne, cloture) ─────────────────────────────
t9 = creer_ticket(
    "Poignée de porte à réparer",
    "Une poignée de porte est desserrée et doit être resserrée/réparée.",
    priorite='faible', statut='cloture', cree_par=karim,
    jour_creation=-27, cout_estime=12, cout_reel=10, jour_cloture=-26,
)
creer_intervention(t9, jour=-26, interne=True, statut='realisee', montant=10,
                    description="Resserrage de la poignée, vis remplacées.")

# ── Cas 10 : verification equipement (a traiter, tres recent) ──────────────
t10 = creer_ticket(
    "Vérification équipement — demande de la direction",
    "Demande de la direction : vérification d'un équipement, à planifier.",
    priorite='normal', statut='a_traiter', cree_par=nathalie,
    jour_creation=-1, cout_estime=None,
)
# Pas d'intervention : ticket tres recent, rien n'a encore ete fait.

print("Enrichissement DEMO-TIL termine.")
for t in [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10]:
    print(f"- {t.titre} | statut={t.get_statut_display()} | responsable={t.responsable}")
print(f"- Prestataire: {ameb.nom}, correspondant local rattache aux Tilleuls")
