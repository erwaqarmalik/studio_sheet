"""
Forms for passport photo generator and user authentication.
"""
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from .widgets import MultipleFileInput
from .utils import PAPER_SIZES


class PassportForm(forms.Form):
    """Form for passport photo generation."""
    photos = forms.FileField(
        widget=MultipleFileInput(attrs={"multiple": True})
    )
    paper_size = forms.ChoiceField(
        choices=[(k, k) for k in PAPER_SIZES.keys()]
    )
    margin_cm = forms.FloatField(initial=1.0)
    gap_cm = forms.FloatField(initial=0.4)
    output_type = forms.ChoiceField(
        choices=[("PDF", "PDF"), ("JPEG", "JPEG")]
    )


class UserProfileForm(forms.ModelForm):
    """
    Extended user profile form with personal details.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    
    class Meta:
        model = UserProfile
        fields = ['date_of_birth', 'phone_number']
        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': 'Date of Birth'
                }
            ),
            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Phone Number (e.g., +1234567890)'
                }
            ),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile
