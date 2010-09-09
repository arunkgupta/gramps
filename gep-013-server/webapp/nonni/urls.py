from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # ORDER MATTERS!
    # Example:
    # (r'^nonni/', include('nonni.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # DANGEROUS in production:
     (r'^styles/(?P<path>.*)$', 'django.views.static.serve',
      {'document_root': 
          '/home/dblank/gramps/gep-013-server/webapp/html/styles', 
       'show_indexes': 
          True},
      ),
     (r'^images/(?P<path>.*)$', 'django.views.static.serve',
      {'document_root': 
          '/home/dblank/gramps/gep-013-server/webapp/html/images', 
       'show_indexes': 
          True},
      ),
    # Uncomment the next line to enable the admin:
     (r'^admin/(.*)', admin.site.root),
    # Finally, root:
     (r'^', 'nonni.home'),
)
