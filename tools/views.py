from .models import Tool, ToolReview
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from .models import Tool, PremiumRequest, ToolReview
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import ToolReviewForm, ToolForm

@login_required
@user_passes_test(lambda u: u.is_superuser)
def tool_update(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    if request.method == 'POST':
        form = ToolForm(request.POST, request.FILES, instance=tool)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tool updated successfully.')
            return redirect(tool.get_absolute_url())
    else:
        form = ToolForm(instance=tool)
    return render(request, 'tools/tool_form.html', {'form': form, 'tool': tool})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def tool_delete(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    if request.method == 'POST':
        tool.delete()
        messages.success(request, 'Tool deleted successfully.')
        return redirect('tools:tools_list')
    else:
        messages.error(request, 'Invalid request method.')
        return redirect(tool.get_absolute_url())

def tools_list(request):
    tools = Tool.objects.all()
    return render(request, 'tools/tools_list.html', {'tools': tools})

@login_required
def tool_detail(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    user_profile = request.user.profile
    if not (user_profile.is_premium or request.user.is_superuser):
        return render(request, 'tools/upgrade_required.html', {'tool': tool})

    reviews = tool.reviews.all()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    if request.method == 'POST':
        if not user_profile.is_premium:
            messages.error(request, 'Only premium users can submit reviews.')
            return redirect(tool.get_absolute_url())
        form = ToolReviewForm(request.POST)
        if form.is_valid():
            review, created = ToolReview.objects.update_or_create(
                tool=tool,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'review_text': form.cleaned_data['review_text'],
                    'created_at': timezone.now(),
                }
            )
            messages.success(request, 'Your review has been submitted.')
            return redirect(tool.get_absolute_url())
    else:
        form = ToolReviewForm()

    context = {
        'tool': tool,
        'reviews': reviews,
        'average_rating': average_rating,
        'form': form,
    }
    return render(request, 'tools/tool_detail.html', context)

@login_required
def request_premium(request):
    user_profile = request.user.profile
    if user_profile.is_premium:
        messages.info(request, 'You are already a premium user.')
        return redirect('tools:tools_list')
    if request.method == 'POST':
        # Check if a pending request already exists
        existing_request = PremiumRequest.objects.filter(user=request.user, status='pending').first()
        if existing_request:
            messages.info(request, 'Your premium request is already pending approval.')
            return redirect('tools:premium_request_status')
        # Create new premium request
        PremiumRequest.objects.create(user=request.user)
        user_profile.premium_request_status = 'pending'
        user_profile.save()
        # Notify admins about new premium request
        admin_emails = [user.email for user in User.objects.filter(is_superuser=True) if user.email]
        if admin_emails:
            send_mail(
                'New Premium Access Request',
                f'User {request.user.username} has requested premium access.',
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True,
            )
        messages.success(request, 'Your request is pending approval.')
        return redirect('tools:premium_request_status')
    return render(request, 'tools/request_premium.html')

@login_required
def premium_request_status(request):
    user_profile = request.user.profile
    status = user_profile.premium_request_status
    return render(request, 'tools/premium_request_status.html', {'status': status})

@login_required
def cancel_premium_request(request):
    user_profile = request.user.profile
    if request.method == 'POST':
        pending_request = PremiumRequest.objects.filter(user=request.user, status='pending').first()
        if pending_request:
            pending_request.status = 'cancelled'
            pending_request.reviewed_at = timezone.now()
            pending_request.save()
            user_profile.premium_request_status = 'cancelled'
            user_profile.save()
            # Send email notification to admins about cancellation
            admin_emails = [user.email for user in User.objects.filter(is_superuser=True) if user.email]
            if admin_emails:
                send_mail(
                    'Premium Access Request Cancelled',
                    f'User {request.user.username} has cancelled their premium access request.',
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
            messages.success(request, 'Your premium request has been cancelled.')
        else:
            messages.info(request, 'No pending premium request found to cancel.')
        return redirect('tools:premium_request_status')
    else:
        messages.error(request, 'Invalid request method.')
        return redirect('tools:premium_request_status')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    from django.contrib.auth.models import User
    from django.db.models import Count
    import datetime
    from django.utils.timezone import now

    requests = PremiumRequest.objects.filter(status='pending').order_by('requested_at')

    total_users = User.objects.count()
    premium_users = User.objects.filter(profile__is_premium=True).count()
    active_requests = PremiumRequest.objects.filter(status='pending').count()
    total_tools = Tool.objects.count()

    # Premium request trends for last 7 days
    today = now().date()
    dates = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    trends = []
    for date in dates:
        count = PremiumRequest.objects.filter(requested_at__date=date).count()
        trends.append({'date': date.strftime('%Y-%m-%d'), 'count': count})

    context = {
        'requests': requests,
        'total_users': total_users,
        'premium_users': premium_users,
        'active_requests': active_requests,
        'total_tools': total_tools,
        'trends': trends,
    }
    return render(request, 'tools/admin_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_request(request, request_id):
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    premium_request.status = 'approved'
    premium_request.reviewed_at = timezone.now()
    premium_request.save()
    user_profile = premium_request.user.profile
    user_profile.is_premium = True
    user_profile.premium_request_status = 'approved'
    user_profile.save()
    # Send email notification to user
    if premium_request.user.email:
        send_mail(
            'Premium Access Approved',
            'Your premium access request has been approved. You now have access to premium tools.',
            settings.DEFAULT_FROM_EMAIL,
            [premium_request.user.email],
            fail_silently=True,
        )
    messages.success(request, f"Premium request for {premium_request.user.username} approved.")
    return redirect(reverse('tools:admin_dashboard'))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_request(request, request_id):
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    premium_request.status = 'rejected'
    premium_request.reviewed_at = timezone.now()
    premium_request.save()
    user_profile = premium_request.user.profile
    user_profile.premium_request_status = 'rejected'
    user_profile.save()
    # Send email notification to user
    if premium_request.user.email:
        send_mail(
            'Premium Access Rejected',
            'Your premium access request has been rejected. Please contact support for more information.',
            settings.DEFAULT_FROM_EMAIL,
            [premium_request.user.email],
            fail_silently=True,
        )
    messages.success(request, f"Premium request for {premium_request.user.username} rejected.")
    return redirect(reverse('tools:admin_dashboard'))
