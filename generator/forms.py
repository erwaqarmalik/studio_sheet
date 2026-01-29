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
    Comprehensive user profile form with complete address and personal details.
    All fields are required.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth',
            'phone_number',
            'street_address',
            'landmark',
            'city',
            'state',
            'postal_code',
            'country',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Date of Birth'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'street_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'House number, street name'
            }),
            'landmark': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nearby landmark (Optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City/Town'
            }),
            'state': forms.Select(attrs={
                'class': 'form-select'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '110001'
            }),
            'country': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        
        # Make landmark optional
        self.fields['landmark'].required = False
    
    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code and not postal_code.isdigit():
            raise forms.ValidationError('Postal code must contain only digits.')
        return postal_code
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        
        # Mark profile as complete
        profile.profile_complete = profile.is_complete()
        
        if commit:
            profile.save()
        return profile
