from django.contrib import admin
from .models import UserSite, LogEntry


class UserSiteAdmin(admin.ModelAdmin):
    list_display = ('user', 'host')    


admin.site.register(UserSite, UserSiteAdmin)


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('site', 'source_url', 'destination_url', 'times', 
                    'time_first', 'time_last')


admin.site.register(LogEntry, LogEntryAdmin)
