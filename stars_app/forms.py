from django import forms

class ChangePasswordForm(forms.Form):
    oldPassword = forms.CharField(widget=forms.PasswordInput())
    newPassword = forms.CharField(widget=forms.PasswordInput())
