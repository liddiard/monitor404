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

def send_error_email(site, source, destination):
    email_message = '''
        Hi %(username)s,

        404monitor detected a HTTP 404 error on %(site)s.

        A user on the page: %(source)s
        clicked on a link to: %(destination)s,
        which resulted in the error.

        For more information, check the %(site)s dashboard on 404monitor:
        %(dashboard_url)s.

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
        '404monitor: 404 Error Detected on %s' % site,
        email_message % context,
        'notification@404monitor.io',
        [user.email],
        fail_silently=False,
        html_message=None
    )


# tasks

@task()
def check_404(source, destination, sites):
    check, created = URLCheck.objects.get_or_create(url=destination)
    if not created: # check already existed
        if check.is_stale():
            check.save() # update the check with the current time
                         # because we're going to check it next...
        else:
            return -1 # url check is fresh; no further processing required
    if is_404(destination):
        for site in sites:
            error, created = LogEntry.objects.get_or_create(site=site, 
                                                         source_url=source, 
                                               destination_url=destination)
            if created:
                send_error_email(site, source, destination)
            else: # it already existed
                error.save()
        return 1 # url 404'd!
    else:
        return 0 # check performed b/c it wasn't cached
