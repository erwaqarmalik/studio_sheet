"""
Forms for passport photo generator and user authentication.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
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


class UserRegistrationForm(UserCreationForm):
    """Extended user registration form with email."""
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        """Save user with email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
