from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from timezone_field import TimeZoneField


class Plan(models.Model):
    name = models.CharField(max_length=32, unique=True)
    max_requests = models.PositiveIntegerField()
    price = models.FloatField()

    def is_free(self):
        return self.price == 0

    def __unicode__(self):
        return self.name


def basic_plan():
    return Plan.objects.get(name='Basic').pk


class UserPrefs(models.Model):
    
    class Meta:
        verbose_name_plural = "User prefs"

    user = models.OneToOneField(User)
    time_zone = TimeZoneField(default='America/Los_Angeles')
    time_zone.help_text = "What time zone should logs display in?"
    email_404 = models.BooleanField(default=True)
    email_404.help_text = "Do you want to be notified of new 404 errors?"
    email_quota = models.BooleanField(default=True)
    email_quota.help_text = '''
        Do you want to be notified if one of your sites goes over its daily 
        request quota?'''
    plan = models.ForeignKey('Plan', default=basic_plan)
    customer = models.CharField(max_length=32, blank=True)

    def __unicode__(self):
        return str(self.user)


class UserSite(models.Model):
    user = models.ForeignKey(User)
    host = models.CharField(max_length=253) # max length of a domain name
    host.help_text = '''
        Full domain name, <strong>including</strong> subdomain (if any), and 
        <strong>excluding</strong> a leading "http://", etc.<br/><br/>Examples: 
        example.com, news.ycombinator.com, www.reddit.com'''
    slug = models.SlugField(max_length=253)
    requests_today = models.PositiveIntegerField(default=0)

    def max_requests(self):
        up = UserPrefs.objects.get_or_create(user=self.user)[0]
        return up.plan.max_requests

    def is_eligible(self):
        return self.requests_today < self.max_requests()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.host)
        super(UserSite, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s: %s" % (self.user, self.host)


class LogEntry(models.Model):

    class Meta:
        verbose_name_plural = "Log entries"

    site = models.ForeignKey(UserSite)
    source_url = models.URLField()
    destination_url = models.URLField()
    time_first = models.DateTimeField(auto_now_add=True)
    time_last = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s > %s" % (self.source_url, self.destination_url)


class URLCheck(models.Model):
    url = models.URLField()
    last_checked = models.DateTimeField(auto_now=True)

    def is_stale(self):
        return self.last_checked + timedelta(hours=1) < datetime.now()

    def __unicode__(self):
        return "%s (%s)" % (self.url, self.last_checked)


class SiteToSkip(models.Model):

    class Meta:
        verbose_name_plural = "Sites to skip"

    host = models.CharField(max_length=253, unique=True)

    def __unicode__(self):
        return self.host
