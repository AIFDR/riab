from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('impact.views',
                       url(r'^calculate/$', 'calculate'),
                       url(r'^layers/$', 'layers'),
                       url(r'^functions/$', 'functions'),
                       )
