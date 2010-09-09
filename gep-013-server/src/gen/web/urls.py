from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from gen.web.grampsdb.views import (main_page, user_page, logout_page,
                                    view, view_detail)

urlpatterns = patterns('',
    # Specific matches first:
    (r'^admin/(.*)', admin.site.root),
)

urlpatterns += patterns('',
    # Static serves! DANGEROUS in production:
     (r'^styles/(?P<path>.*)$', 'django.views.static.serve',
      {'document_root': 
          '/home/dblank/gramps/gep-013-server/src/data', 
       'show_indexes': 
          True},
      ),
     (r'^images/(?P<path>.*)$', 'django.views.static.serve',
      {'document_root': 
          '/home/dblank/gramps/gep-013-server/src/images', 
       'show_indexes': 
          True},
      ),
)

# The rest will match views:
urlpatterns += patterns('',
    (r'^$', main_page),
    (r'^user/(\w+)/$', user_page),
    (r'^login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', logout_page),
    (r'^(?P<view>(\w+))/$', view),
    (r'^(?P<view>(\w+))/(?P<handle>(\w+))/$', view_detail),
)
