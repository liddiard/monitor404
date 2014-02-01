from django.db import models
from django.contrib.auth.models import User


class UserSite(models.Model):
    user = models.ForeignKey(User)
    host = models.CharField(max_length=253) # max length of a domain name

    def __unicode__(self):
        return "%s: %s" % (self.user, self.host)


class LogEntry(models.Model):
    site = models.ForeignKey(UserSite)
    # status_code = models.CharField(max_length=3)
    source_url = models.URLField()
    destination_url = models.URLField()
    time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s > %s" % (self.source_url, self.destination_url)
