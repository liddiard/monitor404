from django.forms import ModelForm
from .models import UserSite, UserPrefs


class UserSiteForm(ModelForm):
    
    class Meta:
        model = UserSite
        fields = ['host']


class UserPrefsForm(ModelForm):

    class Meta:
        model = UserPrefs
        fields = ['timezone', 'email_interval']
