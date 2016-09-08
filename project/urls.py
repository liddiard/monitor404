from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

from monitor import views

urlpatterns = [
    # api
    url(r'^api/check/$', views.MonitorView.as_view()),
    url(r'^api/log/clear/$', views.ClearLogView.as_view()),

    # pages
    url(r'^$', views.FrontView.as_view(), name='front'),
    url(r'^plan/compare/$', views.ComparePlansView.as_view(), name='plan_compare'),
    url(r'^plan/change(?:/(?P<plan>\S+))?/$', views.ChangePlansView.as_view(), name='plan_change'),
    url(r'^plan/charge/$', views.ChargeView.as_view(), name='plan_charge'),
    url(r'^plan/charge/success/$', views.ChargeSuccessView.as_view(), name='plan_charge_success'),
    url(r'^dashboard(?:/(?P<slug>\S+))?/$', views.LogView.as_view(), name='log'),
    url(r'^preferences/$', views.UserPrefsView.as_view(), name='user_prefs'),
    url(r'^site/add/$', views.AddSiteView.as_view(), name='site_add'),
    url(r'^site/remove/(?P<slug>\S+)/$', views.RemoveSiteView.as_view(), 
        name='site_remove'),
    url(r'^docs/$', views.DocsView.as_view(), name='docs'),
    url(r'^demo/$', views.DemoView.as_view(), name='demo'),

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # registration
    url(r'^accounts/', include('project.urls_accounts')),
]