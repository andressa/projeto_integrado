from django.conf.urls.defaults import patterns
import views

urlpatterns = patterns('',
    # Dummy index view
    #(r'^$', views.index),
    (r'^(?P<novela>[\w-]+)/(?P<date>[\w-]+)/(?P<atype>[\w-]+)/$', views.analysis),
)
