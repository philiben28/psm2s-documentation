import traceback
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from registre.models import Utilisateur, DUERP
from registre.views import duerp_signer

try:
    user = Utilisateur.objects.get(username='demo_directeur')
    duerp = DUERP.objects.get(etablissement__code='DEMO-TIL')

    rf = RequestFactory()
    request = rf.post(f'/duerp/{duerp.pk}/signer/')
    request.user = user

    sm = SessionMiddleware(lambda r: None)
    sm.process_request(request)
    request.session.save()

    messages = FallbackStorage(request)
    request._messages = messages

    response = duerp_signer(request, pk=duerp.pk)
    print("OK — statut réponse :", response.status_code)
except Exception:
    print("=== ERREUR CAPTUREE ===")
    traceback.print_exc()
