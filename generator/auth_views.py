"""
Authentication and user management views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.db.models import Count, Sum
from typing import Optional

from .forms import UserRegistrationForm
from .models import PhotoGeneration


def register(request: HttpRequest) -> HttpResponse:
    """
    User registration view.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered registration page or redirect on success
    """
    if request.user.is_authenticated:
        return redirect('generator:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('generator:index')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'generator/register.html', {'form': form})


def user_login(request: HttpRequest) -> HttpResponse:
    """
    User login view.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered login page or redirect on success
    """
    if request.user.is_authenticated:
        return redirect('generator:index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'generator:index')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'generator/login.html', {'form': form})


@login_required
def user_logout(request: HttpRequest) -> HttpResponse:
    """
    User logout view.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Redirect to index page
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('generator:index')


@login_required
def history(request: HttpRequest) -> HttpResponse:
    """
    View user's photo generation history.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered history page with user's generations
    """
    generations = PhotoGeneration.objects.filter(user=request.user)
    
    # Statistics
    stats = {
        'total_generations': generations.count(),
        'total_photos': generations.aggregate(Sum('num_photos'))['num_photos__sum'] or 0,
        'total_copies': generations.aggregate(Sum('total_copies'))['total_copies__sum'] or 0,
        'pdf_count': generations.filter(output_type='PDF').count(),
        'jpeg_count': generations.filter(output_type='JPEG').count(),
    }
    
    context = {
        'generations': generations[:50],  # Limit to 50 most recent
        'stats': stats,
    }
    
    return render(request, 'generator/history.html', context)


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """
    User profile view.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered profile page
    """
    user = request.user
    recent_generations = PhotoGeneration.objects.filter(user=user)[:10]
    
    context = {
        'user': user,
        'recent_generations': recent_generations,
        'total_generations': PhotoGeneration.objects.filter(user=user).count(),
    }
    
    return render(request, 'generator/profile.html', context)
