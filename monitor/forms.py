from django import forms
from .models import UserSite, UserPrefs
from django.contrib.auth import authenticate
from django.shortcuts import redirect


class UserSiteForm(forms.ModelForm):
    
    class Meta:
        model = UserSite
        fields = ['host']


class UserPrefsForm(forms.ModelForm):

    class Meta:
        model = UserPrefs
        fields = ['time_zone', 'email_404', 'email_quota']


class ConfirmCurrentUserForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ConfirmCurrentUserForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ConfirmCurrentUserForm, self).clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None or user != self.request.user:
            raise forms.ValidationError("That username and password are "
                                "incorrect for the currently logged-in user.")
        cleaned_data['user'] = user
        return cleaned_data
