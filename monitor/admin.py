from django.contrib import admin
from .models import UserPrefs, UserSite, LogEntry, URLCheck


class UserPrefsAdmin(admin.ModelAdmin):
    pass


admin.site.register(UserPrefs, UserPrefsAdmin)


class UserSiteAdmin(admin.ModelAdmin):
    list_display = ('user', 'host')    
    prepopulated_fields = {'slug': ('host',)}


admin.site.register(UserSite, UserSiteAdmin)


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('site', 'source_url', 'destination_url', 'time_first', 
                    'time_last')


admin.site.register(LogEntry, LogEntryAdmin)


class URLCheckAdmin(admin.ModelAdmin):
    list_display = ('url', 'last_checked')


admin.site.register(URLCheck, URLCheckAdmin)
