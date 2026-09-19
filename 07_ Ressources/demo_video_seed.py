# ─────────────────────────────────────────────
#  Jeu de données DÉMO pour vidéo de présentation PSM2S (21/08/2026)
#
#  Version enrichie — remplace la version du 05/07/2026 (un seul
#  établissement quasi vide). Objectif : peupler formation avec
#  suffisamment de matière pour filmer une démo convaincante :
#  plusieurs établissements, registre de sécurité avec des statuts
#  variés (vert/orange/rouge), historique, contrats, correspondants
#  locaux, tickets travaux, une commission de sécurité avec
#  prescriptions.
#
#  Rien de réel : établissements, personnes et villes sont inventés.
#  Les organismes de contrôle (SOCOTEC, APAVE, Bureau Veritas, Dekra)
#  sont de vrais organismes du secteur — cohérent avec la décision
#  prise pour la v1 (seuls les NOMS DE PERSONNES doivent être fictifs).
#
#  Idempotent : peut être relancé sans dupliquer (get_or_create partout,
#  sur des clés métier stables).
#
#  Exécution, sur formation, en SSH :
#    DJANGO_SETTINGS_MODULE=config.settings_formation python manage.py shell < demo_video_seed.py
#
#  (transférer d'abord ce fichier vers le serveur — FTP ou Gestionnaire
#  de fichiers cPanel)
# ─────────────────────────────────────────────

import datetime
from registre.models import (
    Etablissement, Batiment, Utilisateur, EtablissementUtilisateur,
    TypeControle, ControleEtablissement, RealisationControle,
    Prestataire, Contrat, CorrespondantLocal,
    TicketTravaux, Intervention,
    VisiteCommission, Prescription, ActionPrescription,
    DUERP, UniteTravail, DroitSignature,
)

today = datetime.date.today()
jours = datetime.timedelta

def j(n):
    """Raccourci : aujourd'hui + n jours (n négatif = dans le passé)."""
    return today + jours(days=n)

# ─────────────────────────────────────────────
# 1. Établissements fictifs
# ─────────────────────────────────────────────

etab_tilleuls, _ = Etablissement.objects.get_or_create(
    code='DEMO-TIL',
    defaults=dict(
        nom="IME Les Tilleuls", type_erp='J', categorie='4',
        adresse="12 rue des Tilleuls", ville="Clairvallon",
        obligation_reglementaire=True, actif=True,
        contact_nom="Nathalie Perrin",
        contact_telephone="02 00 00 00 01",
        contact_email="direction.tilleuls@demo-psm2s.fr",
    )
)
etab_cerisiers, _ = Etablissement.objects.get_or_create(
    code='DEMO-CER',
    defaults=dict(
        nom="EHPAD Les Cerisiers", type_erp='J', categorie='3',
        adresse="8 chemin des Cerisiers", ville="Vallombreuse",
        obligation_reglementaire=True, actif=True,
        contact_nom="Denis Roquet",
        contact_telephone="02 00 00 00 02",
        contact_email="direction.cerisiers@demo-psm2s.fr",
    )
)
etab_vallon, _ = Etablissement.objects.get_or_create(
    code='DEMO-VAL',
    defaults=dict(
        nom="ESAT du Vallon Fleuri", type_erp='J', categorie='4',
        adresse="3 route du Vallon", ville="Bellerive",
        obligation_reglementaire=True, actif=True,
        contact_nom="Isabelle Cordier",
        contact_telephone="02 00 00 00 03",
        contact_email="direction.vallon@demo-psm2s.fr",
    )
)

bat_tilleuls, _ = Batiment.objects.get_or_create(
    etablissement=etab_tilleuls, nom="Bâtiment principal",
    defaults=dict(type_erp='J', categorie='4', capacite_accueil=80, actif=True)
)
bat_cerisiers, _ = Batiment.objects.get_or_create(
    etablissement=etab_cerisiers, nom="Bâtiment principal",
    defaults=dict(type_erp='J', categorie='3', capacite_accueil=120, actif=True)
)
bat_vallon, _ = Batiment.objects.get_or_create(
    etablissement=etab_vallon, nom="Atelier + bureaux",
    defaults=dict(type_erp='J', categorie='4', capacite_accueil=60, actif=True)
)

# ─────────────────────────────────────────────
# 2. Directeur fictif — rattaché uniquement aux Tilleuls
#    (démontre le périmètre restreint d'un compte directeur)
# ─────────────────────────────────────────────

directeur, cree = Utilisateur.objects.get_or_create(
    username='demo_directeur',
    defaults=dict(
        first_name="Nathalie", last_name="Perrin",
        email="nathalie.perrin@demo-psm2s.fr", role='directeur',
    )
)
if cree:
    directeur.set_password('DemoPSM2S2026!')
    directeur.save()
    print("Compte demo_directeur créé — mot de passe : DemoPSM2S2026!")
else:
    print("Compte demo_directeur déjà existant, mot de passe inchangé.")

EtablissementUtilisateur.objects.get_or_create(
    etablissement=etab_tilleuls, utilisateur=directeur, defaults=dict(principal=True)
)

# 2 bis. Factotum fictif — pour montrer le rôle et la délégation interne
#        (niveau 3 : saisie ET signature des interventions)
factotum, cree_f = Utilisateur.objects.get_or_create(
    username='demo_factotum',
    defaults=dict(
        first_name="Karim", last_name="Belhadj",
        email="karim.belhadj@demo-psm2s.fr", role='factotum', niveau_factotum=3,
    )
)
if cree_f:
    factotum.set_password('DemoPSM2S2026!')
    factotum.save()
    print("Compte demo_factotum créé — mot de passe : DemoPSM2S2026!")
else:
    print("Compte demo_factotum déjà existant, mot de passe inchangé.")

EtablissementUtilisateur.objects.get_or_create(
    etablissement=etab_tilleuls, utilisateur=factotum, defaults=dict(principal=True)
)

# ─────────────────────────────────────────────
# 3. Prestataires (réutilisent le référentiel existant — vrais organismes)
# ─────────────────────────────────────────────

socotec = Prestataire.objects.get_or_create_normalise('SOCOTEC')
apave = Prestataire.objects.get_or_create_normalise('APAVE')
veritas = Prestataire.objects.get_or_create_normalise('Bureau Veritas')
dekra = Prestataire.objects.get_or_create_normalise('Dekra Industrial')

# 4. Correspondants locaux fictifs — un par couple (prestataire, établissement),
#    volontairement différents d'un établissement à l'autre (même prestataire,
#    interlocuteur différent : c'est exactement ce que le modèle permet).
correspondants = [
    (socotec, etab_tilleuls, "Julien Faure", "06 00 00 01 02", "j.faure@demo-socotec.fr",
     "Passe généralement le mardi matin. Préfère être appelé sur le portable."),
    (apave, etab_tilleuls, "Camille Roussel", "06 00 00 03 04", "c.roussel@demo-apave.fr",
     "Contact privilégié pour les vérifications électriques."),
    (socotec, etab_cerisiers, "Antoine Berger", "06 00 00 05 06", "a.berger@demo-socotec.fr",
     "Prévenir l'accueil de nuit avant son passage."),
    (veritas, etab_cerisiers, "Marc Delattre", "06 00 00 07 08", "m.delattre@demo-veritas.fr", ""),
    (apave, etab_vallon, "Laure Mercier", "06 00 00 09 10", "l.mercier@demo-apave.fr", ""),
    (dekra, etab_vallon, "Sophie Vasseur", "06 00 00 11 12", "s.vasseur@demo-dekra.fr",
     "Intervient en binôme, prévoir un accès atelier."),
]
for prestataire, etab, nom, tel, email, notes in correspondants:
    CorrespondantLocal.objects.get_or_create(
        prestataire=prestataire, etablissement=etab,
        defaults=dict(nom=nom, telephone=tel, email=email, notes=notes)
    )

# ─────────────────────────────────────────────
# 5. Contrats — répartis sur les 3 établissements, échéances variées
# ─────────────────────────────────────────────

contrats_a_creer = [
    (etab_tilleuls, socotec, 'incendie', "DEMO-CT-001", -200, 165, 850),
    (etab_tilleuls, apave, 'electricite', "DEMO-CT-002", -300, 20, 620),
    (etab_cerisiers, socotec, 'incendie', "DEMO-CT-003", -180, 240, 780),
    (etab_cerisiers, veritas, 'ascenseur', "DEMO-CT-004", -100, 45, 990),
    (etab_vallon, apave, 'electricite', "DEMO-CT-005", -220, 300, 540),
    (etab_vallon, dekra, 'gaz', "DEMO-CT-006", -90, 10, 410),
]
for etab, prest, cat, numero, deb, fin, montant in contrats_a_creer:
    tc = TypeControle.objects.filter(categorie=cat).first()
    Contrat.objects.get_or_create(
        etablissement=etab, prestataire_fk=prest, type_controle=tc,
        defaults=dict(numero=numero, date_debut=j(deb), date_fin=j(fin), montant=montant)
    )

# ─────────────────────────────────────────────
# 6. Contrôles réglementaires — statuts variés par établissement
#    (categorie, statut, jours réalisation, jours échéance, priorité)
# ─────────────────────────────────────────────

plan_controles = {
    etab_tilleuls: [
        ('incendie', 'fait', -60, 305, 'normal'),
        ('incendie', 'a_remettre_a_jour', -350, 15, 'urgent'),
        ('electricite', 'fait', -90, 275, 'normal'),
        ('ascenseur', 'a_faire', None, -15, 'critique'),
        ('exercice', 'fait', -30, 150, 'faible'),
        ('formation', 'a_remettre_a_jour', -320, 45, 'normal'),
        ('document', 'a_faire', None, 5, 'urgent'),
        ('gaz', 'fait', -100, 260, 'normal'),
    ],
    etab_cerisiers: [
        ('incendie', 'fait', -40, 320, 'normal'),
        ('electricite', 'a_remettre_a_jour', -340, 25, 'urgent'),
        ('ascenseur', 'fait', -70, 290, 'normal'),
        ('sanitaire', 'a_faire', None, -5, 'critique'),
        ('exercice', 'fait', -20, 160, 'faible'),
        ('accessibilite', 'a_faire', None, 40, 'normal'),
    ],
    etab_vallon: [
        ('incendie', 'a_remettre_a_jour', -355, 8, 'urgent'),
        ('electricite', 'fait', -80, 280, 'normal'),
        ('gaz', 'a_faire', None, -20, 'critique'),
        ('exercice', 'fait', -45, 140, 'faible'),
        ('formation', 'fait', -15, 350, 'normal'),
    ],
}
batiment_par_etab = {etab_tilleuls: bat_tilleuls, etab_cerisiers: bat_cerisiers, etab_vallon: bat_vallon}

controles_crees = []
for etab, lignes in plan_controles.items():
    bat = batiment_par_etab[etab]
    for cat, statut, jr, je, priorite in lignes:
        tc = TypeControle.objects.filter(categorie=cat).first()
        if not tc:
            continue
        controle, _ = ControleEtablissement.objects.get_or_create(
            etablissement=etab, batiment=bat, type_controle=tc,
            defaults=dict(
                statut=statut,
                date_realisation=j(jr) if jr is not None else None,
                prochaine_echeance=j(je),
                priorite=priorite,
            )
        )
        controles_crees.append(controle)

# ─────────────────────────────────────────────
# 7. Historique de réalisations — 2 années sur 2 contrôles des Tilleuls
#    (pour montrer la navigation par année du registre)
# ─────────────────────────────────────────────

controle_incendie_til = ControleEtablissement.objects.filter(
    etablissement=etab_tilleuls, type_controle__categorie='incendie', statut='fait'
).first()
if controle_incendie_til:
    for annee, decalage in [(today.year - 2, -790), (today.year - 1, -425), (today.year, -60)]:
        RealisationControle.objects.get_or_create(
            controle=controle_incendie_til, annee=annee,
            defaults=dict(date_realisation=j(decalage), statut='fait', organisme='SOCOTEC')
        )

# ─────────────────────────────────────────────
# 8. Tickets travaux — sur les Tilleuls, workflow varié
# ─────────────────────────────────────────────

controle_ascenseur_til = ControleEtablissement.objects.filter(
    etablissement=etab_tilleuls, type_controle__categorie='ascenseur'
).first()
controle_document_til = ControleEtablissement.objects.filter(
    etablissement=etab_tilleuls, type_controle__categorie='document'
).first()

ticket1, _ = TicketTravaux.objects.get_or_create(
    etablissement=etab_tilleuls, titre="Remise en service ascenseur bâtiment principal",
    defaults=dict(
        controle=controle_ascenseur_til,
        description="Ascenseur bloqué en position ouverte depuis le contrôle périodique. Intervention Otis à planifier en urgence.",
        priorite='critique', statut='devis_demande',
        date_cible=j(10), cout_estime=1200,
    )
)
ticket2, _ = TicketTravaux.objects.get_or_create(
    etablissement=etab_tilleuls, titre="Mise à jour du registre de sécurité incendie",
    defaults=dict(
        controle=controle_document_til,
        description="Compléter le registre suite à la dernière visite de la commission de sécurité.",
        priorite='urgent', statut='en_cours', date_cible=j(3),
    )
)
ticket3, _ = TicketTravaux.objects.get_or_create(
    etablissement=etab_tilleuls, titre="Remplacement extincteur hall d'entrée",
    defaults=dict(
        description="Extincteur non conforme remplacé lors du dernier passage SOCOTEC.",
        priorite='normal', statut='cloture', date_cible=j(-30),
        date_cloture=datetime.datetime.now() - jours(days=25), cout_reel=95,
    )
)
Intervention.objects.get_or_create(
    ticket=ticket3, prestataire='SOCOTEC', date_intervention=j(-28),
    defaults=dict(description="Remplacement extincteur à poudre 6kg, hall d'entrée.", statut='realisee', montant=95)
)

# ─────────────────────────────────────────────
# 9. Commission de sécurité — visite + prescriptions (Tilleuls)
# ─────────────────────────────────────────────

visite, _ = VisiteCommission.objects.get_or_create(
    etablissement=etab_tilleuls, date_visite=j(-95),
    defaults=dict(
        date_pv=j(-80),
        observations="Visite périodique. Avis favorable sous réserve de la levée des prescriptions ci-dessous.",
    )
)
presc1, _ = Prescription.objects.get_or_create(
    visite=visite, numero="1",
    defaults=dict(
        description="Ascenseur : remettre en service et fournir le rapport de contrôle technique.",
        delai=j(15), statut='en_cours', ticket=ticket1,
    )
)
presc2, _ = Prescription.objects.get_or_create(
    visite=visite, numero="2",
    defaults=dict(
        description="Extincteur du hall d'entrée non conforme : à remplacer.",
        delai=j(-40), statut='levee', ticket=ticket3,
    )
)
ActionPrescription.objects.get_or_create(
    prescription=presc2, type_action='travaux_realises', date=j(-28),
    defaults=dict(note="Extincteur remplacé par SOCOTEC, justificatif joint au ticket.")
)
ActionPrescription.objects.get_or_create(
    prescription=presc1, type_action='devis_demande', date=j(-8),
    defaults=dict(note="Devis Otis demandé pour remise en service.")
)

# ─────────────────────────────────────────────
# 10. DUERP des Tilleuls — pour montrer la signature électronique
# ─────────────────────────────────────────────

duerp, _ = DUERP.objects.get_or_create(
    etablissement=etab_tilleuls, annee=today.year,
    defaults=dict(
        statut='valide',
        signataire="Nathalie Perrin",
        observations_generales="Document unique mis à jour lors de la revue annuelle.",
    )
)
for type_unite, ordre in [('internat', 1), ('maintenance_entretien', 2)]:
    UniteTravail.objects.get_or_create(duerp=duerp, type_unite=type_unite, defaults=dict(ordre=ordre))

# Droit de signature du DUERP pour le directeur démo — sans ce droit,
# le bouton "Signer" n'apparaît pas pour un directeur (seuls
# admin/responsable_securite l'ont automatiquement, cf. DroitSignature.peut_signer).
DroitSignature.objects.get_or_create(
    utilisateur=directeur, etablissement=etab_tilleuls, document='duerp'
)

print("Démo prête :")
print(" -", etab_tilleuls, "| connexion directeur : demo_directeur / DemoPSM2S2026!")
print(" -", etab_tilleuls, "| connexion factotum (niveau 3) : demo_factotum / DemoPSM2S2026!")
print(" -", etab_cerisiers)
print(" -", etab_vallon)
print(f" - {len(controles_crees)} contrôles créés au total sur les 3 établissements")
print(" - 3 tickets travaux, 1 visite de commission avec 2 prescriptions (Tilleuls)")
print(" - 1 DUERP Tilleuls, droit de signature accordé à demo_directeur")
print(" - Pense à téléverser une image de signature sur le profil demo_directeur ou")
print("   demo_factotum avant le tournage, pour pouvoir démontrer la signature électronique.")

# ─────────────────────────────────────────────
#  SUPPRESSION — à lancer séparément si besoin de nettoyer après tournage
#  (ne PAS lancer en même temps que le script ci-dessus)
#
#  from registre.models import Etablissement, Utilisateur
#  Etablissement.objects.filter(code__in=['DEMO-TIL', 'DEMO-CER', 'DEMO-VAL']).delete()
#  Utilisateur.objects.filter(username='demo_directeur').delete()
#
#  Cascade : bâtiments, contrats, contrôles, correspondants locaux, tickets,
#  interventions, visites de commission, prescriptions.
#  Ne supprime pas SOCOTEC / APAVE / Bureau Veritas / Dekra (référentiel
#  partagé, potentiellement utilisé par de vrais établissements).
# ─────────────────────────────────────────────
