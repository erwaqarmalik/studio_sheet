"""
Forms for passport photo generator and user authentication.
"""
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, PhotoConfiguration
from .widgets import MultipleFileInput
from .utils import PAPER_SIZES
from .config import PHOTO_SIZES


class PassportForm(forms.Form):
    """Form for passport photo generation with variable sizes."""
    photos = forms.FileField(
        widget=MultipleFileInput(attrs={"multiple": True}),
        help_text="Select one or more photos"
    )
    paper_size = forms.ChoiceField(
        choices=[(k, k) for k in PAPER_SIZES.keys()]
    )
    margin_cm = forms.FloatField(initial=1.0)
    gap_cm = forms.FloatField(initial=0.4)
    output_type = forms.ChoiceField(
        choices=[("PDF", "PDF"), ("JPEG", "JPEG")]
    )
    
    # Global default photo size (can be overridden per photo)
    default_photo_size = forms.ChoiceField(
        choices=[(k, v["label"]) for k, v in PHOTO_SIZES.items()],
        initial="passport_35x45",
        help_text="Default photo size for all photos"
    )
    
    default_copies = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=6,
        help_text="Default number of copies per photo"
    )


class PhotoConfigurationForm(forms.ModelForm):
    """Form for configuring individual photo size and copies."""
    
    class Meta:
        model = PhotoConfiguration
        fields = ['photo_size', 'custom_width_cm', 'custom_height_cm', 'copies']
        widgets = {
            'photo_size': forms.Select(attrs={
                'class': 'form-select photo-size-select'
            }),
            'custom_width_cm': forms.NumberInput(attrs={
                'class': 'form-control custom-width',
                'placeholder': 'Width (cm)',
                'min': 1,
                'max': 20,
                'step': 0.1,
                'style': 'display: none;'
            }),
            'custom_height_cm': forms.NumberInput(attrs={
                'class': 'form-control custom-height',
                'placeholder': 'Height (cm)',
                'min': 1,
                'max': 20,
                'step': 0.1,
                'style': 'display: none;'
            }),
            'copies': forms.NumberInput(attrs={
                'class': 'form-control copies-input',
                'min': 1,
                'max': 100
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        photo_size = cleaned_data.get('photo_size')
        custom_width = cleaned_data.get('custom_width_cm')
        custom_height = cleaned_data.get('custom_height_cm')
        
        if photo_size == 'custom':
            if not custom_width or not custom_height:
                raise forms.ValidationError(
                    "Both width and height are required for custom size."
                )
        
        return cleaned_data


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
