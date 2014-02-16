from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from monitor import views

urlpatterns = patterns('',
    # api
    url(r'^api/check/$', views.MonitorView.as_view()),
    url(r'^api/log/clear/$', views.ClearLogView.as_view()),

    # pages
    url(r'^$', views.FrontView.as_view(), name='front'),
    url(r'^plan/change/$', views.ChangePlanView.as_view(), name='plan_change'),
    url(r'^dashboard(?:/(?P<slug>\S+))?/$', views.LogView.as_view(), name='log'),
    url(r'^preferences/$', views.UserPrefsView.as_view(), name='user_prefs'),
    url(r'^site/add/$', views.AddSiteView.as_view(), name='site_add'),
    url(r'^site/remove/(?P<slug>\S+)/$', views.RemoveSiteView.as_view(), 
        name='site_remove'),
    url(r'^demo/$', views.DemoView.as_view(), name='demo'),

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # registration
    (r'^accounts/', include('project.urls_accounts')),
)
