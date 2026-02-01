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
from typing import Optional

from .models import PhotoGeneration, DeletionHistory


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
    
    return JsonResponse({
        'success': True,
        'message': 'Record deleted successfully. You can restore it from the deleted items view.'
    })


@login_required
@require_http_methods(["POST"])
def restore_generation(request: HttpRequest, generation_id: int) -> JsonResponse:
    """
    Restore a soft-deleted photo generation record.
    
    Args:
        request: Django HTTP request
        generation_id: ID of the generation to restore
    
    Returns:
        JSON response with success status
    """
    generation = get_object_or_404(PhotoGeneration.all_objects, pk=generation_id, user=request.user)
    
    if not generation.is_deleted():
        return JsonResponse({'success': False, 'error': 'Record is not deleted'}, status=400)
    
    reason = request.POST.get('reason', 'User requested restoration')
    generation.restore(restored_by=request.user, reason=reason)
    
    return JsonResponse({
        'success': True,
        'message': 'Record restored successfully.'
    })


@login_required
def deletion_history_view(request: HttpRequest) -> HttpResponse:
    """
    View deletion history for the current user.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Rendered deletion history page
    """
    # Get user's generation IDs
    user_generation_ids = PhotoGeneration.all_objects.filter(
        user=request.user
    ).values_list('id', flat=True)
    
    # Get deletion history for user's generations (don't slice yet)
    history_queryset = DeletionHistory.objects.filter(
        model_name='PhotoGeneration',
        object_id__in=user_generation_ids
    ).select_related('performed_by').order_by('-performed_at')
    
    # Calculate statistics before slicing
    stats = {
        'total_deletions': history_queryset.filter(action='delete').count(),
        'total_restorations': history_queryset.filter(action='restore').count(),
        'total_hard_deletes': history_queryset.filter(action='hard_delete').count(),
        'total_operations': history_queryset.count(),
    }
    
    # Now slice for display
    history_records = history_queryset[:100]
    
    context = {
        'history_records': history_records,
        'stats': stats,
    }
    
    return render(request, 'generator/deletion_history.html', context)
