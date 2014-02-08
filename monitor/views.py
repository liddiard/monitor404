import json
import urllib2
from urlparse import urlparse
from django.http import HttpResponse, Http404
from django.views.generic.base import View, TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import UserPrefs, UserSite, LogEntry, URLCheck
from .forms import UserSiteForm, UserPrefsForm


# pages

class FrontView(TemplateView):

    template_name = "front.html"


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


class AddSiteView(TemplateView):

    template_name = "site_add.html"

    def post(self, request):
        form = UserSiteForm(request.POST)
        if form.is_valid():
            host = form.cleaned_data['host']
            UserSite.objects.get_or_create(host=host, user=request.user)
            return redirect('log')
        else:
            return redirect('site_add')

    def get_context_data(self, **kwargs):
        context = super(AddSiteView, self).get_context_data(**kwargs)
        context['form'] = UserSiteForm
        return context


class RemoveSiteView(TemplateView):

    template_name = "site_remove.html"

    def post(self, request, **kwargs):
        context = self.get_context_data()
        context['site'].delete()
        return redirect('log')

    def get_context_data(self, **kwargs):
        context = super(RemoveSiteView, self).get_context_data(**kwargs)
        site_slug = self.kwargs.get('slug')
        context['site'] = get_object_or_404(UserSite, slug=site_slug, 
                                            user=self.request.user)
        return context


class UserPrefsView(TemplateView):

    template_name = "user_prefs.html"

    def post(self, request):
        form = UserPrefsForm(request.POST)
        if form.is_valid():
            prefs = UserPrefs.objects.get(user=self.request.user)
            prefs.timezone = form.cleaned_data['timezone']
            prefs.email_interval = form.cleaned_data['email_interval']
            prefs.save() 
            return redirect('log')
        else:
            return redirect('user_prefs')

    def get_context_data(self, **kwargs):
        context = super(UserPrefsView, self).get_context_data(**kwargs)
        prefs = UserPrefs.objects.get_or_create(user=self.request.user)[0]
        context['form'] = UserPrefsForm(instance=prefs)
        return context


class DemoView(TemplateView):
    
    template_name = "demo.html"


# abstract base classes

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


# api

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
        if not created: # check already existed
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
