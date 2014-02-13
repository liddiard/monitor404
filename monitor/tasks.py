from __future__ import absolute_import
import urllib2

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
            if not created: # it already existed
                error.save()
        # send an email
        return 1 # url 404'd!
    else:
        return 0 # check performed b/c it wasn't cached
