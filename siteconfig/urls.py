from django.conf.urls.defaults import patterns, include, url
import cc_mining.urls
import novela.urls

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include(cc_mining.urls)),
    url(r'novelas/', include(novela.urls)),
)
