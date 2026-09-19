# ─────────────────────────────────────────────
#  CONTRAT-CADRE AMEB MULTISERVICES — DEMO-TIL
#
#  Cree un seul objet : le Contrat qui relie AMEB Multiservices (deja
#  existant) a DEMO-TIL, pour qu'il apparaisse dans le referentiel
#  Partenaires. Ne touche a rien d'autre : ni Prestataire, ni
#  CorrespondantLocal, ni aucun TicketTravaux/Intervention existant.
#
#  Idempotent : cle de lookup stable = numero de contrat (jamais de date
#  relative dans la cle).
#
#  Execution, sur formation, en SSH (venv active) :
#    DJANGO_SETTINGS_MODULE=config.settings_formation python manage.py shell < contrat_cadre_ameb.py
# ─────────────────────────────────────────────

import datetime
from registre.models import Etablissement, Utilisateur, Prestataire, Contrat

etab = Etablissement.objects.get(code='DEMO-TIL')
nathalie = Utilisateur.objects.get(username='demo_directeur')
ameb = Prestataire.objects.get(nom='AMEB Multiservices')

contrat, cree = Contrat.objects.get_or_create(
    numero='CONV-AMEB-2026',
    defaults=dict(
        etablissement=etab,
        prestataire_fk=ameb,
        type_controle=None,
        date_debut=datetime.date(2026, 1, 1),
        date_fin=datetime.date(2026, 12, 31),
        montant=None,
        notes=(
            "Convention-cadre pour interventions ponctuelles de maintenance "
            "courante (électricité, plomberie, petits travaux)."
        ),
        cree_par=nathalie,
    )
)

print("Contrat créé :" if cree else "Contrat déjà existant, inchangé :")
print(f"- {contrat.numero} | {contrat.prestataire_fk.nom} | {contrat.etablissement.code} "
      f"| {contrat.date_debut} → {contrat.date_fin}")
