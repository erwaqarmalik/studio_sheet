"""
Authentication and user management views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from typing import Optional

from .models import PhotoGeneration, DeletionHistory, AdminActivity, SystemMaintenance, UserProfile


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
                messages.success(request, f'Welcome back, {user.first_name}{" "}{user.last_name}!')
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
    View user's photo generation history (including deleted records).
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered history page with user's generations
    """
    # Get filter parameter
    show_deleted = request.GET.get('show_deleted', 'active')
    
    if show_deleted == 'deleted':
        # Show only deleted records
        generations = PhotoGeneration.all_objects.filter(user=request.user, deleted_at__isnull=False)
    elif show_deleted == 'all':
        # Show all records (active + deleted)
        generations = PhotoGeneration.all_objects.filter(user=request.user)
    else:
        # Default: show only active records
        generations = PhotoGeneration.objects.filter(user=request.user)
    
    # Statistics
    stats = {
        'total_generations': PhotoGeneration.objects.filter(user=request.user).count(),
        'deleted_generations': PhotoGeneration.all_objects.filter(user=request.user, deleted_at__isnull=False).count(),
        'total_photos': PhotoGeneration.objects.filter(user=request.user).aggregate(Sum('num_photos'))['num_photos__sum'] or 0,
        'total_copies': PhotoGeneration.objects.filter(user=request.user).aggregate(Sum('total_copies'))['total_copies__sum'] or 0,
        'pdf_count': PhotoGeneration.objects.filter(user=request.user, output_type='PDF').count(),
        'jpeg_count': PhotoGeneration.objects.filter(user=request.user, output_type='JPEG').count(),
    }
    
    context = {
        'generations': generations.order_by('-created_at')[:50],  # Limit to 50 most recent
        'stats': stats,
        'show_deleted': show_deleted,
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


@login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    """
    Edit user profile.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered edit profile page or redirect on success
    """
    user = request.user
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', '').strip()
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        new_password_confirm = request.POST.get('new_password_confirm', '')
        
        errors = []
        
        # Validate basic info
        if not first_name:
            errors.append('First name is required.')
        
        if not last_name:
            errors.append('Last name is required.')
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            errors.append('Email already exists.')
        
        # Validate password change if provided
        if new_password or new_password_confirm or current_password:
            if not current_password:
                errors.append('Current password is required to change password.')
            elif not user.check_password(current_password):
                errors.append('Current password is incorrect.')
            elif not new_password:
                errors.append('New password is required.')
            elif len(new_password) < 8:
                errors.append('New password must be at least 8 characters long.')
            elif new_password != new_password_confirm:
                errors.append('New passwords do not match.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Update basic info
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                
                # Update or create profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.phone_number = phone_number
                profile.street_address = street_address
                profile.landmark = landmark
                profile.city = city
                profile.state = state
                profile.postal_code = postal_code
                profile.country = country
                profile.save()
                
                # Update password if provided
                if new_password:
                    user.set_password(new_password)
                    messages.success(request, 'Password updated successfully. Please login again.')
                
                user.save()
                
                # Log activity
                AdminActivity.objects.create(
                    action_type='admin_action',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'action': 'profile_updated', 'description': f'Updated profile: {user.username}'}
                )
                
                if new_password:
                    # Re-authenticate if password changed
                    return redirect('generator:login')
                else:
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('generator:profile')
                    
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
    
    context = {
        'user': user,
    }
    
    return render(request, 'generator/edit_profile.html', context)


@login_required
@require_http_methods(["POST"])
def soft_delete_generation(request: HttpRequest, generation_id: int) -> JsonResponse:
    """
    Soft delete a photo generation record.
    
    Args:
        request: Django HTTP request
        generation_id: ID of the generation to delete
    
    Returns:
        JSON response with success status
    """
    generation = get_object_or_404(PhotoGeneration.all_objects, pk=generation_id, user=request.user)
    
    if generation.is_deleted():
        return JsonResponse({'success': False, 'error': 'Record is already deleted'}, status=400)
    
    reason = request.POST.get('reason', 'User requested deletion')
    generation.delete(deleted_by=request.user, reason=reason)
    
    # Log to AdminActivity
    try:
        AdminActivity.objects.create(
            action_type='delete',
            user=request.user,
            ip_address=get_client_ip(request),
            details={
                'generation_id': generation_id,
                'output_type': generation.output_type,
                'reason': reason,
            }
        )
    except Exception as e:
        # Log error but don't fail the delete
        pass
    
    return JsonResponse({
        'success': True,
        'message': 'Record deleted successfully.'
    })


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# NOTE: restore_generation endpoint removed - admin-only restoration via Django admin panel
# NOTE: deletion_history_view removed - users no longer see deletion history


@login_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Admin dashboard with live request monitoring and system statistics.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered admin dashboard page
    """
    # Check if user is admin/staff
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('generator:index')
    
    # Get system maintenance settings
    settings = SystemMaintenance.get_settings()
    
    # Get recent activities (last 50)
    recent_activities = AdminActivity.objects.all()[:50]
    
    # Calculate statistics
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats = {
        'total_users': PhotoGeneration.objects.values('user').distinct().count(),
        'total_generations': PhotoGeneration.objects.count(),
        'active_generations': PhotoGeneration.objects.filter(deleted_at__isnull=True).count(),
        'deleted_generations': PhotoGeneration.all_objects.filter(deleted_at__isnull=False).count(),
        'total_files_mb': (PhotoGeneration.objects.aggregate(Sum('file_size_bytes'))['file_size_bytes__sum'] or 0) / (1024 * 1024),
        'today_generations': PhotoGeneration.objects.filter(created_at__date=today.date()).count(),
        'activity_today': AdminActivity.objects.filter(timestamp__date=today.date()).count(),
    }
    
    # Activity breakdown
    activity_breakdown = AdminActivity.objects.values('action_type').annotate(count=Count('action_type'))
    
    # Recent users who generated photos (today)
    recent_users = PhotoGeneration.objects.filter(
        created_at__date=today.date()
    ).values('user__username').annotate(count=Count('id')).order_by('-count')[:10]
    
    context = {
        'settings': settings,
        'recent_activities': recent_activities,
        'stats': stats,
        'activity_breakdown': list(activity_breakdown),
        'recent_users': list(recent_users),
    }
    
    return render(request, 'generator/admin_dashboard.html', context)


@login_required
def create_user(request: HttpRequest) -> HttpResponse:
    """
    Create new user account (admin only).
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered user creation form or redirect on success
    """
    # Check if user is admin/staff
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to create users.')
        return redirect('generator:index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        is_staff = request.POST.get('is_staff') == 'on'
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if not first_name:
            errors.append('First name is required.')
        
        if not last_name:
            errors.append('Last name is required.')
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already exists.')
        
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if password != password_confirm:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                )
                
                # Log admin activity
                AdminActivity.objects.create(
                    action_type='admin_action',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={
                        'action': 'user_created',
                        'description': f'Created user: {username} ({first_name} {last_name})',
                        'username': username,
                        'is_staff': is_staff
                    }
                )
                
                messages.success(request, f'User "{username}" created successfully!')
                return redirect('generator:manage_users')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'generator/create_user.html')


@login_required
def manage_users(request: HttpRequest) -> HttpResponse:
    """
    Manage users list (admin only).
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered user management page
    """
    # Check if user is admin/staff
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to manage users.')
        return redirect('generator:index')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Calculate stats
    stats = {
        'total_users': users.count(),
        'admin_users': users.filter(is_staff=True).count(),
        'active_users': users.filter(is_active=True).count(),
        'logged_in_users': users.filter(last_login__isnull=False).count(),
    }
    
    context = {
        'users': users,
        'stats': stats,
    }
    
    return render(request, 'generator/manage_users.html', context)


@login_required
def generation_status(request: HttpRequest, session_id: str) -> JsonResponse:
    """Return generation status for a session."""
    generation = get_object_or_404(PhotoGeneration.all_objects, session_id=session_id, user=request.user)
    return JsonResponse({
        'status': generation.status,
        'output_url': generation.output_url,
        'error_message': generation.error_message,
    })
