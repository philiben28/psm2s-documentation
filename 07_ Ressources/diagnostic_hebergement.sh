#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  DIAGNOSTIC HEBERGEMENT PSM2S — 100% LECTURE SEULE
#
#  Ne modifie AUCUN fichier, ne redémarre AUCUN service,
#  n'installe et ne desinstalle RIEN.
#  Une seule requete reseau optionnelle en fin de script :
#  un GET sur votre propre URL publique pour verifier si Cle.txt
#  est accessible depuis l'exterieur (pas un scan d'infrastructure,
#  juste un test cible sur notre propre application).
#
#  A executer DEPUIS le dossier de l'instance a auditer
#  (celui qui contient manage.py), en SSH, venv active.
#
#  Exemple pour formation :
#    cd ~/formation.psm2s.pbci-conseils.fr   (ou le chemin equivalent)
#    source ~/virtualenv/.../3.9/bin/activate   (comme d'habitude)
#    bash diagnostic_hebergement.sh
#
#  A relancer ensuite dans le dossier de PRODUCTION de la meme facon,
#  pour comparer les deux configurations.
# ─────────────────────────────────────────────────────────────

echo "================================================================"
echo " DIAGNOSTIC HEBERGEMENT PSM2S — $(date)"
echo " Dossier courant : $(pwd)"
echo "================================================================"

echo ""
echo "--- 1. Version Python reellement utilisee ---"
which python
python --version 2>&1

echo ""
echo "--- 2. Version Django reellement installee ---"
python -c "import django; print('Django', django.get_version())" 2>&1
echo "Detail pip :"
pip show django 2>&1 | grep -E "Name|Version|Location"

echo ""
echo "--- 3, 4, 9, 10. Parametres Django actifs (SSL, HSTS, base, comptes admin) ---"
echo "  (lu directement via manage.py shell, donc tel que Django le voit reellement)"
python manage.py shell -c "
from django.conf import settings
import os

print('DJANGO_SETTINGS_MODULE =', os.environ.get('DJANGO_SETTINGS_MODULE'))
print()
print('DEBUG =', settings.DEBUG)
print('SECURE_SSL_REDIRECT =', settings.SECURE_SSL_REDIRECT)
print('SESSION_COOKIE_SECURE =', settings.SESSION_COOKIE_SECURE)
print('CSRF_COOKIE_SECURE =', settings.CSRF_COOKIE_SECURE)
print('SECURE_HSTS_SECONDS =', settings.SECURE_HSTS_SECONDS)
print('Variable env DJANGO_SSL (telle que vue par ce process) =', os.environ.get('DJANGO_SSL'))
print('Variable env DJANGO_HSTS_SECONDS (telle que vue par ce process) =', os.environ.get('DJANGO_HSTS_SECONDS'))
print()
print('DATABASES =', settings.DATABASES)
print('BASE_DIR =', settings.BASE_DIR)
print()
from registre.models import Utilisateur
print('Comptes avec is_staff=True :')
for u in Utilisateur.objects.filter(is_staff=True):
    print(f'  - {u.username} | is_superuser={u.is_superuser} | actif={u.is_active}')
print()
print('Comptes avec is_superuser=True :')
for u in Utilisateur.objects.filter(is_superuser=True):
    print(f'  - {u.username}')
" 2>&1

echo ""
echo "--- 5. Configuration Passenger reellement utilisee ---"
echo "Contenu de passenger_wsgi.py :"
cat passenger_wsgi.py 2>&1
echo ""
echo "Contenu de .htaccess (si present, souvent la ou Passenger est configure sur cPanel) :"
cat .htaccess 2>&1

echo ""
echo "--- 6. Presence de Cle.txt et permissions ---"
ls -la Cle.txt 2>&1
if [ -f "Cle.txt" ]; then
    echo "Cle.txt existe. Taille et droits ci-dessus."
    echo "ATTENTION : contenu NON affiche ici volontairement (fichier potentiellement sensible)."
fi

echo ""
echo "--- 7. Droits sur les fichiers sensibles ---"
for f in config/settings.py config/settings_formation.py manage.py Cle.txt db.sqlite3 db_formation.sqlite3 .env; do
    if [ -e "$f" ]; then
        ls -la "$f"
    fi
done

echo ""
echo "--- 8. Fichiers .env, sauvegardes, archives potentiellement exposes ---"
echo "(recherche limitee a ce dossier et ses sous-dossiers directs, lecture seule)"
find . -maxdepth 3 \( \
    -iname "*.env*" -o \
    -iname "*.bak" -o \
    -iname "*backup*" -o \
    -iname "*.zip" -o \
    -iname "*.sql" -o \
    -iname "*.sqlite3*" -o \
    -iname "*.tar.gz" \
    \) 2>/dev/null | grep -v "^\./venv" | grep -v "^\./virtualenv"

echo ""
echo "--- 9 (suite). Emplacement et droits du fichier SQLite ---"
find . -maxdepth 2 -iname "*.sqlite3*" -exec ls -la {} \;

echo ""
echo "--- 11. Indices sur une eventuelle politique de sauvegarde automatisee ---"
echo "Taches planifiees (cron) visibles pour cet utilisateur :"
crontab -l 2>&1
echo ""
echo "Dossiers de sauvegarde eventuels a la racine du compte :"
ls -la ~ 2>&1 | grep -iE "backup|save|archive"

echo ""
echo "--- 6 (suite). Test d'accessibilite publique de Cle.txt (une seule requete, lecture seule) ---"
echo "Ce test envoie une requete HTTP HEAD vers votre propre site, rien d'autre."
if command -v curl >/dev/null 2>&1; then
    for url in "https://formation.psm2s.pbci-conseils.fr/Cle.txt" "https://psm2s.pbci-conseils.fr/Cle.txt"; do
        echo "Test : $url"
        curl -s -o /dev/null -w "  -> code HTTP : %{http_code}\n" "$url" 2>&1
    done
else
    echo "curl non disponible sur ce serveur, test ignore."
fi

echo ""
echo "================================================================"
echo " FIN DU DIAGNOSTIC. Copier-coller l'integralite de cette sortie."
echo "================================================================"
