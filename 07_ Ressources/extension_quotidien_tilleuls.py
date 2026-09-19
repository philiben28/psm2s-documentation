# ─────────────────────────────────────────────
#  EXTENSION donnees demo Tilleuls — vie quotidienne du batiment
#  (fontaines, podotactile, eclairage, plomberie)
#
#  Idempotent : cles de lookup stables (titre du ticket, jamais de date
#  relative dans une clé get_or_create — lecon retenue de la duplication
#  precedente sur VisiteCommission/Intervention).
#
#  NE TOUCHE QUE DEMO-TIL. Aucune reference aux autres etablissements.
#
#  A executer proche de la date de tournage (dates calculees par
#  rapport a aujourd'hui).
#
#  Execution, sur formation, en SSH (venv active) :
#    DJANGO_SETTINGS_MODULE=config.settings_formation python manage.py shell < extension_quotidien_tilleuls.py
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

etab = Etablissement.objects.get(code='DEMO-TIL')
nathalie = Utilisateur.objects.get(username='demo_directeur')
karim = Utilisateur.objects.get(username='demo_factotum')

# ── Cas 3 & 4 : nouveau prestataire "du quotidien" ──────────────────────────
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
        nom="Yannick Ferreira", telephone="06 00 00 21 22", email="y.ferreira@ameb-multiservices.fr",
        notes="Intervient sous 48h en général, prévenir l'accueil avant son passage.",
    )
)

# ── Cas 1 : fontaines a eau (interne, cloture) ──────────────────────────────
t1, _ = TicketTravaux.objects.get_or_create(
    etablissement=etab, titre="Réapprovisionnement consommables fontaines à eau",
    defaults=dict(
        description="Stock de gobelets et filtres des fontaines à eau du bâtiment principal proche de zéro, à renouveler avant rupture.",
        priorite='faible', statut='cloture',
        responsable=karim, cree_par=karim,
        date_cible=j(-3), cout_estime=40, cout_reel=35,
        date_cloture=timezone.now() - jours(days=2),
    )
)
Intervention.objects.get_or_create(
    ticket=t1,
    defaults=dict(
        realise_en_interne=True, date_intervention=j(-2),
        description="Réapprovisionnement effectué directement, commande passée auprès du fournisseur habituel de consommables.",
        statut='realisee', montant=35, saisie_par=karim,
    )
)

# ── Cas 2 : bande podotactile (interne, securite, cloture) ─────────────────
t2, _ = TicketTravaux.objects.get_or_create(
    etablissement=etab, titre="Bande podotactile décollée - escalier bâtiment principal",
    defaults=dict(
        description="Bande de vigilance podotactile partiellement décollée en haut de l'escalier principal, risque de chute.",
        priorite='urgent', statut='cloture',
        responsable=karim, cree_par=nathalie,
        date_cible=j(-5), cout_estime=15, cout_reel=12,
        date_cloture=timezone.now() - jours(days=4),
    )
)
Intervention.objects.get_or_create(
    ticket=t2,
    defaults=dict(
        realise_en_interne=True, date_intervention=j(-4),
        description="Recollage de la bande avec colle spécifique, vérification de l'adhérence.",
        statut='realisee', montant=12, saisie_par=karim,
    )
)

# ── Cas 3 : eclairage (externe AMEB, cloture) ───────────────────────────────
t3, _ = TicketTravaux.objects.get_or_create(
    etablissement=etab, titre="Éclairage défaillant - couloir bâtiment principal",
    defaults=dict(
        description="Plusieurs points lumineux hors service dans le couloir menant aux chambres, ballast probablement à remplacer.",
        priorite='normal', statut='cloture',
        responsable=karim, cree_par=karim,
        date_cible=j(-7), cout_estime=110, cout_reel=95,
        date_cloture=timezone.now() - jours(days=6),
    )
)
Intervention.objects.get_or_create(
    ticket=t3,
    defaults=dict(
        prestataire='AMEB Multiservices', date_intervention=j(-6),
        description="Remplacement de 2 ballasts électroniques et d'un tube néon.",
        statut='realisee', montant=95, saisie_par=karim,
    )
)

# ── Cas 4 : plomberie (externe AMEB, EN COURS — pas cloture) ───────────────
t4, _ = TicketTravaux.objects.get_or_create(
    etablissement=etab, titre="Fuite robinetterie - sanitaires bâtiment principal",
    defaults=dict(
        description="Fuite au niveau du mitigeur d'un lavabo, sanitaire du rez-de-chaussée.",
        priorite='urgent', statut='en_cours',
        responsable=karim, cree_par=nathalie,
        date_cible=j(2), cout_estime=55,
        # cout_reel et date_cloture volontairement vides : pas encore termine
    )
)
Intervention.objects.get_or_create(
    ticket=t4,
    defaults=dict(
        prestataire='AMEB Multiservices', date_intervention=j(2),
        description="Devis reçu, intervention planifiée pour remplacement du mitigeur.",
        statut='planifiee', saisie_par=karim,
        # montant volontairement vide : pas encore facture, seul le devis (cout_estime=55) existe
    )
)

print("Extension terminee.")
print(f"- {t1.titre} | statut={t1.get_statut_display()}")
print(f"- {t2.titre} | statut={t2.get_statut_display()}")
print(f"- {t3.titre} | statut={t3.get_statut_display()}")
print(f"- {t4.titre} | statut={t4.get_statut_display()} (volontairement non cloture)")
print(f"- Prestataire: {ameb.nom}, correspondant local rattache aux Tilleuls")
