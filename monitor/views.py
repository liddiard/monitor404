import urllib2
import json
from django.http import HttpResponse
from django.views.generic.base import View, TemplateView

from .models import UserSite, LogEntry


class FrontView(TemplateView):
    pass


class DemoView(TemplateView):
    
    template_name = "demo.html"


class AjaxView(View):

    def dispatch(self, request, *args, **kwargs):
        if request.is_ajax():
            return super(AjaxView, self).dispatch(request, *args, **kwargs)
        else:
            raise Http404

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
        host = request.META.get('HTTP_HOST')
        try:
           sites = UserSite.objects.filter(host=host) 
        except UserSite.DoesNotExist:
            return self.does_not_exist('UserSite matching host %s was not '
                                       'found.' % host)
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
