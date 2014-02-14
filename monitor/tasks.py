from __future__ import absolute_import
import urllib2

from django.core.urlresolvers import reverse
from django.core.mail import send_mail

# from celery import shared_task
from celery.task import task

from .models import URLCheck, LogEntry


# utils

def is_404(url):
    request = urllib2.Request(url)
    request.get_method = lambda : 'HEAD'
    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        return e.code == 404
    else:
        return False

def send_error_email(source, destination, site):
    email_message = '''
        Hi %(username)s,

        404monitor detected a HTTP 404 error on %(site)s.

        A user on the page: %(source)s
        clicked on a link to: %(destination)s,
        which resulted in the error.

        For more information, check the %(site)s dashboard on 404monitor:
        http://404monitor.io%(dashboard_url)s.

        Thanks,
        The 404monitor team
    '''

    context = {
        'username': site.user.username,
        'site': site.host,
        'source': source,
        'destination': destination,
        'dashboard_url': reverse('log', args=(site.slug,))
    }

    send_mail(
        '404monitor: 404 Error Detected on %s' % site.host,
        email_message % context,
        'notification@404monitor.io',
        [site.user.email],
        fail_silently=False,
    )


# tasks

@task()
def check_404(source, destination, sites):
    eligible_site = False
    for site in sites:
        if site.is_eligible():
            site.requests_today += 1
            site.save()
            eligible_site = True
    if not eligible_site:
        return -2 # no eligible sites
    check, created = URLCheck.objects.get_or_create(url=destination)
    if not created: # check already existed
        if check.is_stale():
            check.save() # update the check with the current time
                         # because we're going to check it next...
        else:
            return -1 # url check is fresh; no further processing required
    if is_404(destination):
        for site in sites:
            if site.is_eligible():
                error, created = LogEntry.objects.get_or_create(site=site, 
                                                             source_url=source, 
                                                   destination_url=destination)
                if created:
                    send_error_email(source, destination, site)
                else: # it already existed
                    error.save()
        return 1 # url 404'd!
    else:
        return 0 # check performed b/c it wasn't cached

@task()
def clear_cache_and_requests_count():
    ''' should be run once a day, preferably during low-traffic hours'''
    all_sites = UserSite.objects.all()
    for site in all_sites:
        site.requests_today = 0
        site.save()
    URLCheck.objects.all().delete()
    return 0
