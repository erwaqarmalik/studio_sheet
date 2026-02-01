"""
Authentication and user management views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from typing import Optional

from .models import PhotoGeneration, DeletionHistory, AdminActivity, SystemMaintenance


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
