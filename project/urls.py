from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from monitor import views

urlpatterns = patterns('',
    # api
    url(r'^api/check/$', views.MonitorView.as_view()),

    # pages
    url(r'^$', views.FrontView.as_view(), name='front'),
    url(r'^sites/$', views.SitesView.as_view(), name='sites'),
    url(r'^log/$', views.LogView.as_view(), name='log'),
    url(r'^demo/$', views.DemoView.as_view(), name='demo'),

    # admin
    url(r'^admin/', include(admin.site.urls)),
)
