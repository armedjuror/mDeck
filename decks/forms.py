from allauth.account.forms import SignupForm
from django import forms


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label='First name',
        widget=forms.TextInput(attrs={'placeholder': 'First name', 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        max_length=30,
        label='Last name',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last name (optional)', 'autocomplete': 'family-name'}),
    )

    # Put name fields first
    field_order = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save(update_fields=['first_name', 'last_name'])
        return user
