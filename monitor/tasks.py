from __future__ import absolute_import
import urllib2
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.core.mail import send_mail

# from celery import shared_task
from celery.task import task

from .models import URLCheck, LogEntry, UserPrefs, SiteToSkip


# utils

def is_404(url):
    request = urllib2.Request(url)
    request.get_method = lambda : 'HEAD'
    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        return e.code == 404
    except: # catchall other url errors
        return None # falsy value
    else:
        return False

def send_error_email(source, destination, site):
    email_message = '''
Hi %(username)s,

monitor404 just detected a HTTP 404 error on %(site)s.

A user on the page: %(source)s
clicked on a link to: %(destination)s,
which resulted in the error.

For more information, check the %(site)s dashboard on 404monitor:
http://monitor404.com%(dashboard_url)s.

Thanks,
The monitor404 team
    '''

    context = {
        'username': site.user.username,
        'site': site.host,
        'source': source,
        'destination': destination,
        'dashboard_url': reverse('log', args=(site.slug,))
    }

    send_mail(
        'Error detected on %s' % site.host,
        email_message % context,
        'monitor404 <notification@monitor404.com>',
        [site.user.email],
        fail_silently=False,
    )

def send_quota_email(site):
    email_message = '''
Hi %(username)s,

We wanted you to know that your site, %(site)s, reached its limit of 
%(max_requests)s link checks today, which means it won't be checking links 
for 404 errors for the rest of the day.

To get more requests, you can change your plan to Premium or Enterprise to get 
10x or 100x as many requests per day, respectively. Take a look at plan 
options and pricing here: 
%(plan_change_url)s.

If you'd prefer to not receive emails when one of your sites exceeds its quota, 
you can change your notification preferences here:
http://monitor404.com%(user_prefs_url)s.

Thanks,
The monitor404 team
    '''

    context = {
        'username': site.user.username,
        'site': site.host,
        'max_requests': site.max_requests,
        'plan_change_url': reverse('plan_change'),
        'user_prefs_url': reverse('user_prefs')
    }

    send_mail(
        'Over quota on %s' % site.host,
        email_message % context,
        'monitor404 <notification@monitor404.com>',
        [site.user.email],
        fail_silently=False,
    )


# tasks

@task()
def check_404(source, destination, sites):
    eligible_site = False
    for site in sites:
        if site.is_eligible():
            eligible_site = True
            break
    if not eligible_site:
        print -3
        return -3 # no eligible sites

    destination_host = urlparse(destination).netloc
    site_to_skip = False
    for site in SiteToSkip.objects.all():
        if site.host == destination_host:
            site_to_skip = True
            break
    if site_to_skip:
        print -2
        return -2 # site is stored in db as one to skip

    check, created = URLCheck.objects.get_or_create(url=destination)
    if not created: # check already existed
        if check.is_stale():
            check.save() # update the check with the current time
                         # because we're going to check it next...
        else:
            print -1
            return -1 # url check is fresh; no further processing required

    if is_404(destination):
        for site in sites:
            if site.is_eligible():
                site.requests_today += 1
                site.save()
                error, created = LogEntry.objects.get_or_create(site=site, 
                                                             source_url=source, 
                                                   destination_url=destination)
                if created:
                    prefs = UserPrefs.objects.get_or_create(user=site.user)[0]
                    if prefs.email_404:
                        send_error_email(source, destination, site)
                else: # it already existed
                    error.save()
                if not site.is_eligible(): # site just reached quota
                    prefs = UserPrefs.objects.get_or_create(user=site.user)[0]
                    if prefs.email_quota:
                        send_quota_email(site)
        print 1
        return 1 # url 404'd!
    else:
        print 0
        return 0 # check performed b/c it wasn't cached
