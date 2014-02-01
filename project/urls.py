from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from monitor import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^api/check/$', views.MonitorView.as_view()),
    url(r'^demo/$', views.DemoView.as_view(), name='demo'),
    url(r'^admin/', include(admin.site.urls)),
)
