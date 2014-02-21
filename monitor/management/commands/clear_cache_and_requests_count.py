from django.core.management.base import BaseCommand, CommandError

from monitor.models import UserSite, URLCheck


class Command(BaseCommand):
    
    def handle(self, *args, **options):
        ''' should be run once a day, preferably during low-traffic hours'''
        all_sites = UserSite.objects.all()
        for site in all_sites:
            site.requests_today = 0
            site.save()
        URLCheck.objects.all().delete()
        return 0
