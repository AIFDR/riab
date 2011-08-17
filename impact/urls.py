from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
                       url(r'^$',
                           'django.views.generic.simple.direct_to_template',
                           {'template': 'impact/calculator.html'},
                           name='calculator'))

urlpatterns += patterns('impact.views',
                       url(r'^api/calculate/$', 'calculate'),
                       url(r'^api/layers/$', 'layers'),
                       url(r'^api/functions/$', 'functions'),
                       url(r'^api/debug/$', 'debug'))
