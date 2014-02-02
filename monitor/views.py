import json
import urllib2
from urlparse import urlparse
from django.http import HttpResponse, Http404
from django.views.generic.base import View, TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from .models import UserSite, LogEntry, URLCheck


class FrontView(TemplateView):

    template_name = "front.html"


class SitesView(TemplateView):
    
    template_name = "sites.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SitesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SitesView, self).get_context_data(**kwargs)
        context['sites'] = UserSite.objects.filter(user=self.request.user)
        return context


class LogView(TemplateView):
    
    template_name = "log.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LogView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LogView, self).get_context_data(**kwargs)
        site_slug = self.kwargs.get('slug')
        if site_slug is None:
            try:
                site = UserSite.objects.filter(user=self.request.user).last()
            except UserSite.DoesNotExist:
                site = None
        else:
            site = get_object_or_404(UserSite, slug=site_slug, 
                                     user=self.request.user)
        context['site'] = site
        context['sites'] = UserSite.objects.filter(user=self.request.user)
        context['entries'] = LogEntry.objects.filter(site=site)\
                                     .order_by('-time_last')
        return context


class DemoView(TemplateView):
    
    template_name = "demo.html"


class AjaxView(View):

    def json_response(self, **kwargs):
        return HttpResponse(json.dumps(kwargs), content_type="application/json")

    def success(self, **kwargs):
        return self.json_response(result=0, **kwargs)

    def error(self, error_type, message):
        return self.json_response(result=1, error=error_type, message=message)

    def authentication_error(self):
        return self.error("AuthenticationError", "User is not authenticated.")

    def access_error(self, message):
        return self.error("AccessError", message)

    def key_error(self, message):
        return self.error("KeyError", message)

    def does_not_exist(self, message):
        return self.error("DoesNotExist", message)

    def validation_error(self, message):
        return self.error("ValidationError", message)


class MonitorView(AjaxView):
    
    def get(self, request):
        destination = request.GET.get('destination')
        if destination is None:
            return self.key_error('Required key "destination" not found in '
                                  'request.')
        source = request.GET.get('source')
        if source is None:
            return self.key_error('Required key "source" not found in request.')
        origin = request.META.get('HTTP_ORIGIN')
        try:
            host = urlparse(origin).netloc
        except: # NOTICE: catchall
            return self.error(error="URLError", 
                              message='Could not parse origin header URL %s.' %\
                              origin)
        sites = UserSite.objects.filter(host=host) 
        if not sites:
            return self.does_not_exist('UserSite matching host %s was not '
                                       'found.' % host)
        check, created = URLCheck.objects.get_or_create(url=destination)
        if not created:
            if check.is_stale():
                check.save()
            else:
                return self.success(message='URL check is fresh; aborting.')
        if self.is_404(destination):
            for site in sites:
                error, created = LogEntry.objects.get_or_create(site=site, 
                                                             source_url=source, 
                                                   destination_url=destination)
                if not created: # it already existed
                    error.times += 1
                    error.save()
            return self.success(error404=1)
            # send an email
        else:
            return self.success(error404=0)

    def is_404(self, url):
        request = urllib2.Request(url)
        request.get_method = lambda : 'HEAD'
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if e.code == 404:
                return True
            else:
                return False
        else:
            return False
