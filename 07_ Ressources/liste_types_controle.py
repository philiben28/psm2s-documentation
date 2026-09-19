# Liste (lecture seule) du catalogue des types de controle PSM2S
from registre.models import TypeControle

types = TypeControle.objects.all().order_by('categorie', 'nom')
categorie_actuelle = None
for t in types:
    if t.categorie != categorie_actuelle:
        categorie_actuelle = t.categorie
        print(f"\n=== {t.get_categorie_display()} ===")
    periodicite = t.periodicite.libelle if t.periodicite else "—"
    obligatoire = "obligatoire" if t.obligatoire else "facultatif"
    print(f"- {t.nom}" + (f" ({t.type_action})" if t.type_action else "") + f" | periodicite={periodicite} | {obligatoire}")

print(f"\nTotal : {types.count()} type(s) de controle en base")
