# Create your views here.
from django.http import HttpResponse
from django.conf import settings

def index(request):
    return HttpResponse('CC Mining comming soon. This is a %s environment'
                        % settings.DJANGO_DEPLOY_ENV)
