from django.conf.urls.defaults import patterns, url
from cc_mining.views import *

urlpatterns = patterns('',
   (r'^$', index),
   url(r'^jornalismo/$', Jornalismo, name='jornalismo'),
   url(r'^copa/$', Copa, name='copa'),
)
