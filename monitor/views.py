import json
from urlparse import urlparse

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse, Http404
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings

import stripe
stripe.api_key = settings.STRIPE_API_KEY

from .tasks import check_404
from .models import UserPrefs, UserSite, LogEntry, URLCheck, Plan, SiteToSkip
from .forms import UserSiteForm, UserPrefsForm, ConfirmCurrentUserForm

# abstract base classes

class SidebarView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(SidebarView, self).get_context_data(**kwargs)
        context['sites'] = UserSite.objects.filter(user=self.request.user)
        return context


# pages

class FrontView(TemplateView):

    template_name = "front.html"


class LogView(SidebarView):
    
    template_name = "log.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LogView, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        context = self.get_context_data()
        site_slug = self.kwargs.get('slug')
        if site_slug is None:
            try:
                site = UserSite.objects.filter(user=self.request.user).last()
            except UserSite.DoesNotExist:
                site = None
        else:
            site = get_object_or_404(UserSite, slug=site_slug, 
                                     user=self.request.user)
        if site and not site.is_eligible():
            messages.warning(request, '%s has reached your daily request quota '
                             'limit for the day and is no longer checking '
                             'links for errors. Protect your site against '
                             'new 404s by <a href="%s">upgrading your '
                             'plan</a>.' % (site.host, 
                             reverse_lazy('plan_compare')))
        try:
            user_prefs = UserPrefs.objects.get(user=self.request.user)
        except UserPrefs.DoesNotExist:
            messages.info(request, 'Welcome to monitor404! Save your '
                          'preferences to get started.')
            return redirect('user_prefs')
        context['user_tz'] = user_prefs.time_zone
        context['site'] = site
        context['entries'] = LogEntry.objects.filter(site=site)\
                                     .order_by('-time_last')
        return self.render_to_response(context)


class AddSiteView(SidebarView):

    template_name = "site_add.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddSiteView, self).dispatch(*args, **kwargs)

    def post(self, request):
        form = UserSiteForm(request.POST)
        if form.is_valid():
            host = form.cleaned_data['host']
            UserSite.objects.get_or_create(host=host, user=request.user)
            messages.success(request, '%s was added!' % host)
            return redirect('log')
        else:
            return redirect('site_add')

    def get_context_data(self, **kwargs):
        context = super(AddSiteView, self).get_context_data(**kwargs)
        context['form'] = UserSiteForm
        return context


class RemoveSiteView(SidebarView):

    template_name = "site_remove.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemoveSiteView, self).dispatch(*args, **kwargs)

    def post(self, request, **kwargs):
        context = self.get_context_data()
        site = context['site']
        site.delete()
        messages.success(request, '%s was removed.' % site.host)
        return redirect('log')

    def get_context_data(self, **kwargs):
        context = super(RemoveSiteView, self).get_context_data(**kwargs)
        site_slug = self.kwargs.get('slug')
        context['site'] = get_object_or_404(UserSite, slug=site_slug, 
                                            user=self.request.user)
        return context


class UserPrefsView(SidebarView):

    template_name = "user_prefs.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserPrefsView, self).dispatch(*args, **kwargs)

    def post(self, request):
        form = UserPrefsForm(request.POST)
        if form.is_valid():
            prefs = UserPrefs.objects.get(user=self.request.user)
            prefs.time_zone = form.cleaned_data['time_zone']
            prefs.email_404 = form.cleaned_data['email_404']
            prefs.email_quota = form.cleaned_data['email_quota']
            prefs.save() 
            messages.success(request, 'Preferences updated.')
            return redirect('log')
        else:
            return redirect('user_prefs')

    def get_context_data(self, **kwargs):
        context = super(UserPrefsView, self).get_context_data(**kwargs)
        prefs = UserPrefs.objects.get_or_create(user=self.request.user)[0]
        context['user_prefs'] = prefs
        context['form'] = UserPrefsForm(instance=prefs)
        return context


class DemoView(TemplateView):
    
    template_name = "demo.html"


class ComparePlansView(SidebarView):
    
    template_name = "plan_compare.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ComparePlansView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ComparePlansView, self).get_context_data(**kwargs)
        context['plans'] = Plan.objects.all().order_by('price')
        context['user_prefs'] = UserPrefs.objects\
                                    .get_or_create(user=self.request.user)[0]
        return context


class ChangePlansView(SidebarView):
    
    template_name = "plan_change.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if self.kwargs.get('plan') is None:
            return redirect('plan_compare')
        return super(ChangePlansView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ChangePlansView, self).get_context_data(**kwargs)
        plan_slug = self.kwargs.get('plan')
        context['plan'] = get_object_or_404(Plan, name__iexact=plan_slug)
        context['user_prefs'] = UserPrefs.objects\
                                      .get_or_create(user=self.request.user)[0]
        return context


class ChargeView(SidebarView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ChargeView, self).dispatch(*args, **kwargs)

    def post(self, request):
        plan = request.POST.get('plan')
        stripe_plan = "monitor404_" + plan
        user_prefs = UserPrefs.objects.get_or_create(user=request.user)[0]

        if user_prefs.customer:
            customer = stripe.Customer.retrieve(user_prefs.customer)
            subscription_id = customer['subscriptions']['data'][0]['id']
            subscription = customer.subscriptions.retrieve(subscription_id)
            subscription.plan = stripe_plan
            subscription.save()
        else:
            token = request.POST.get('stripeToken')
            try:
                customer = stripe.Customer.create(
                    email=user_prefs.user.email,
                    description=user_prefs.user.username,
                    plan=stripe_plan,
                    card=token
                )
            except stripe.error.CardError as e:
                error_msg = e.json_body['error']['message']
                messages.error(request, 'Whoops! '+error_msg)
                return redirect('plan_change', plan=plan)
            else:
                customer_id = customer['subscriptions']['data'][0]['customer']
                user_prefs.customer = customer_id
                user_prefs.save()
        p = Plan.objects.get(name__iexact=plan)
        user_prefs.plan = p
        user_prefs.save()
        return redirect('plan_charge_success')


class ChargeSuccessView(TemplateView):

    template_name = "plan_charge_success.html"

    def get_context_data(self, **kwargs):
        context = super(ChargeSuccessView, self).get_context_data(**kwargs)
        context['user_prefs'] = UserPrefs.objects\
                                    .get_or_create(user=self.request.user)[0]
        print context
        return context


class DocsView(TemplateView):

    template_name = "docs.html"

    def get_context_data(self, **kwargs):
        context = super(DocsView, self).get_context_data(**kwargs)
        context['sites_to_skip'] = SiteToSkip.objects.all()
        return context


class AccountDeleteView(FormView):

    template_name = "registration/account_delete_form.html" 
    form_class = ConfirmCurrentUserForm
    success_url = reverse_lazy('account_delete_complete')

    def get_form_kwargs(self):
        kwargs = super(AccountDeleteView, self).get_form_kwargs()
        kwargs.update({
            'request' : self.request
        })
        return kwargs

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AccountDeleteView, self).dispatch(*args, **kwargs)
    
    def form_valid(self, form):
        user = form.cleaned_data.get('user')
        UserSite.objects.filter(user=user).delete()
        user.is_active = False
        user.save()
        django_logout(self.request)
        return redirect('account_delete_complete')


class AccountDeleteCompleteView(TemplateView):
    
    template_name = "registration/account_delete_complete.html"


# abstract base classes

class AjaxView(View):

    def json_response(self, **kwargs):
        return HttpResponse(json.dumps(kwargs), content_type="application/json")

    def success(self, **kwargs):
        return self.json_response(result=0, **kwargs)

    def error(self, error, message):
        return self.json_response(result=1, error=error, message=message)

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


class AuthenticatedAjaxView(AjaxView):
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return super(AuthenticatedAjaxView, self).dispatch(request, *args,
                                                               **kwargs)
        else:
            return self.authentication_error()


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
            return self.error('URLError', 'Could not parse origin header URL '
                              '"%s."' % origin)
        sites = UserSite.objects.filter(host=host) 
        if not sites:
            return self.does_not_exist('UserSite matching host "%s" was not '
                                       'found.' % host)
        check_404.delay(source, destination, sites)
        return self.success(status='success', message='Link queued for check.')


class ClearLogView(AuthenticatedAjaxView):
    
    def post(self, request):
        slug = request.POST.get('slug')
        try:
            us = UserSite.objects.get(slug=slug, user=request.user)
        except UserSite.DoesNotExist:
            return self.does_not_exist('UserSite matching slug "%s" does not '
                                       'exist for the current user.' % slug)
        LogEntry.objects.filter(site=us).delete()
        return self.success(message='Log entries for site %s deleted.' % slug)
