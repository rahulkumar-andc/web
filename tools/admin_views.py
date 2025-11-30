from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from .models import Tool, PremiumRequest, ToolReview
from django.contrib.auth.models import User
from django.utils import timezone

@login_required
@user_passes_test(lambda u: u.is_superuser)
def custom_admin_dashboard(request):
    # Overview stats
    total_tools = Tool.objects.count()
    total_users = User.objects.count()
    premium_users = User.objects.filter(profile__is_premium=True).count()
    pending_requests = PremiumRequest.objects.filter(status='pending').count()

    context = {
        'total_tools': total_tools,
        'total_users': total_users,
        'premium_users': premium_users,
        'pending_requests': pending_requests,
    }
    return render(request, 'tools/admin_panel/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_tools(request):
    tools = Tool.objects.all()
    return render(request, 'tools/admin_panel/manage_tools.html', {'tools': tools})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_premium_requests(request):
    requests = PremiumRequest.objects.all().order_by('-requested_at')
    return render(request, 'tools/admin_panel/manage_premium_requests.html', {'requests': requests})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_premium_request(request, request_id):
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    premium_request.status = 'approved'
    premium_request.reviewed_at = timezone.now()
    premium_request.save()
    user_profile = premium_request.user.profile
    user_profile.is_premium = True
    user_profile.premium_request_status = 'approved'
    user_profile.save()
    messages.success(request, f"Premium request for {premium_request.user.username} approved.")
    return redirect(reverse('tools:custom_admin_dashboard'))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_premium_request(request, request_id):
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    premium_request.status = 'rejected'
    premium_request.reviewed_at = timezone.now()
    premium_request.save()
    user_profile = premium_request.user.profile
    user_profile.premium_request_status = 'rejected'
    user_profile.save()
    messages.success(request, f"Premium request for {premium_request.user.username} rejected.")
    return redirect(reverse('tools:custom_admin_dashboard'))
