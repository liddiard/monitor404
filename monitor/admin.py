from django.contrib import admin
from .models import UserPrefs, UserSite, LogEntry, URLCheck, Plan, SiteToSkip


class PlanAdmin(admin.ModelAdmin):
    pass


admin.site.register(Plan, PlanAdmin)


class UserPrefsAdmin(admin.ModelAdmin):
    pass


admin.site.register(UserPrefs, UserPrefsAdmin)


class UserSiteAdmin(admin.ModelAdmin):
    list_display = ('host', 'user')    
    prepopulated_fields = {'slug': ('host',)}


admin.site.register(UserSite, UserSiteAdmin)


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('site', 'source_url', 'destination_url', 'time_first', 
                    'time_last')


admin.site.register(LogEntry, LogEntryAdmin)


class URLCheckAdmin(admin.ModelAdmin):
    list_display = ('url', 'last_checked')


admin.site.register(URLCheck, URLCheckAdmin)


class SiteToSkipAdmin(admin.ModelAdmin):
    pass


admin.site.register(SiteToSkip, SiteToSkipAdmin)
