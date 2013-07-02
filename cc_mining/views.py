# Create your views here.
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect

import json
import datetime

from cc_mining.models import *

def index(request):
    return render_to_response('index.html',
                              {},
                              context_instance=RequestContext(request)
                              )

@csrf_protect
def Jornalismo(request):
    result = {"JN": ""}
    since = datetime.datetime.strptime(request.POST['date'], '%d/%m/%Y')
    until = since + datetime.timedelta(days=1)
    closed_captions = CC.objects.filter(tvshow__pid__name='JN', tvshow__date__lte=until, tvshow__date__gte=since)
    for cc in closed_captions:
        try:
            result["JN"] += cc.text.split(": ")[1]
        except IndexError:
            result["JN"] += cc.text
    return HttpResponse(json.dumps(result))
