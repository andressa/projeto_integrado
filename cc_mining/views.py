# Create your views here.
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from novela.views import get_novelas, get_dates

def index(request):
    return render_to_response('index.html',
                            { 'novelas_list': get_novelas(), 'dates_list': get_dates()},
                              context_instance=RequestContext(request)
                              )
