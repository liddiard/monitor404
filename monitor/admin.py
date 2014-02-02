from django.contrib import admin
from .models import UserPreferences, UserSite, LogEntry


class UserPreferencesAdmin(admin.ModelAdmin):
    pass


admin.site.register(UserPreferences, UserPreferencesAdmin)


class UserSiteAdmin(admin.ModelAdmin):
    list_display = ('user', 'host')    
    prepopulated_fields = {'slug': ('host',)}


admin.site.register(UserSite, UserSiteAdmin)


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('site', 'source_url', 'destination_url', 'times', 
                    'time_first', 'time_last')


admin.site.register(LogEntry, LogEntryAdmin)
