# Create your views here.
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request):
    return render_to_response('index.html',
                              {},
                              context_instance=RequestContext(request)
                              )
