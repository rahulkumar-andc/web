from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from .models import Tool, PremiumRequest, ToolReview
from .forms import ToolReviewForm, ToolForm
from core.models import CustomUser, SecurityLog
from core.decorators import contributor_required, moderator_required, admin_required
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def log_security_event(user, action, request, details=None):
    SecurityLog.objects.create(
        user=user,
        action=action,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        details=details or {}
    )


@login_required
@contributor_required
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
@moderator_required
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
    if request.user.is_authenticated and (request.user.is_moderator() or request.user.is_superuser):
        tools = Tool.objects.all()
    else:
        tools = Tool.objects.filter(is_approved=True)
    return render(request, 'tools/tools_list.html', {'tools': tools})


@login_required
def tool_detail(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    user = request.user
    if not (user.is_premium or user.is_superuser):
        return render(request, 'tools/upgrade_required.html', {'tool': tool})

    reviews = tool.reviews.all()
    average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

    if request.method == 'POST':
        if not user.is_premium:
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
    user = request.user
    if user.is_premium:
        messages.info(request, 'You are already a premium user.')
        return redirect('tools:premium_request_status')
    if request.method == 'POST':
        existing_request = PremiumRequest.objects.filter(user=request.user, status='pending').first()
        if existing_request:
            messages.info(request, 'Your premium request is already pending approval.')
            return redirect('tools:premium_request_status')
        
        requested_tier = request.POST.get('tier', 'basic')
        requested_duration = int(request.POST.get('duration', 30))
        request_reason = request.POST.get('reason', '').strip()
        
        PremiumRequest.objects.create(
            user=request.user,
            requested_tier=requested_tier,
            requested_duration=requested_duration,
            request_reason=request_reason,
            ip_address=get_client_ip(request)
        )
        user.premium_request_status = 'pending'
        user.save()
        
        log_security_event(
            user=user,
            action='premium_request',
            request=request,
            details={
                'status': 'pending',
                'tier': requested_tier,
                'duration': requested_duration
            }
        )
        
        admin_emails = [u.email for u in CustomUser.objects.filter(is_superuser=True) if u.email]
        if admin_emails:
            try:
                send_mail(
                    'New Premium Access Request',
                    f'User {request.user.username} has requested {requested_tier.upper()} premium access for {requested_duration} days.',
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'Failed to send premium request email: {e}')
        messages.success(request, 'Your request is pending approval.')
        return redirect('tools:premium_request_status')
    
    tier_choices = PremiumRequest.TIER_CHOICES
    duration_choices = PremiumRequest.DURATION_CHOICES
    return render(request, 'tools/request_premium.html', {
        'tier_choices': tier_choices,
        'duration_choices': duration_choices
    })


@login_required
def premium_request_status(request):
    user = request.user
    status = user.premium_request_status
    latest_request = PremiumRequest.objects.filter(user=user).first()
    
    context = {
        'status': status,
        'user': user,
        'latest_request': latest_request,
        'is_premium': user.is_premium,
        'premium_tier': user.get_premium_tier_display_name() if hasattr(user, 'get_premium_tier_display_name') else 'Free',
        'days_remaining': user.get_premium_days_remaining() if hasattr(user, 'get_premium_days_remaining') else 0,
        'expires_at': user.premium_expires_at,
    }
    return render(request, 'tools/premium_request_status.html', context)


@login_required
def cancel_premium_request(request):
    user = request.user
    if request.method == 'POST':
        pending_request = PremiumRequest.objects.filter(user=request.user, status='pending').first()
        if pending_request:
            pending_request.status = 'cancelled'
            pending_request.reviewed_at = timezone.now()
            pending_request.save()
            user.premium_request_status = 'cancelled'
            user.save()
            
            log_security_event(
                user=user,
                action='premium_cancelled',
                request=request,
                details={'request_id': pending_request.id}
            )
            
            admin_emails = [u.email for u in CustomUser.objects.filter(is_superuser=True) if u.email]
            if admin_emails:
                try:
                    send_mail(
                        'Premium Access Request Cancelled',
                        f'User {request.user.username} has cancelled their premium access request.',
                        settings.DEFAULT_FROM_EMAIL,
                        admin_emails,
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f'Failed to send cancellation email: {e}')
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
    from django.db.models import Count
    import datetime
    from django.utils.timezone import now

    requests = PremiumRequest.objects.filter(status='pending').order_by('requested_at')

    total_users = CustomUser.objects.count()
    premium_users = CustomUser.objects.filter(is_premium=True).count()
    active_requests = PremiumRequest.objects.filter(status='pending').count()
    total_tools = Tool.objects.count()

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
    from core.models import PremiumHistory
    from datetime import timedelta
    
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    
    if not premium_request.is_pending():
        messages.warning(request, f"Request is already {premium_request.get_status_display().lower()}.")
        return redirect(reverse('tools:admin_dashboard'))
    
    approved_tier = request.POST.get('approved_tier', premium_request.requested_tier)
    approved_duration = int(request.POST.get('approved_duration', premium_request.requested_duration))
    admin_notes = request.POST.get('admin_notes', '').strip()
    
    premium_request.status = 'approved'
    premium_request.reviewed_at = timezone.now()
    premium_request.reviewed_by = request.user
    premium_request.approved_tier = approved_tier
    premium_request.approved_duration = approved_duration
    if admin_notes:
        premium_request.admin_notes = admin_notes
    premium_request.save()
    
    user = premium_request.user
    previous_tier = user.premium_tier
    
    user.is_premium = True
    user.premium_request_status = 'approved'
    user.premium_tier = approved_tier
    user.premium_activated_at = timezone.now()
    
    if approved_duration > 0:
        user.premium_expires_at = timezone.now() + timedelta(days=approved_duration)
    else:
        user.premium_expires_at = None
    
    user.save()
    
    PremiumHistory.objects.create(
        user=user,
        action='activated',
        previous_tier=previous_tier,
        new_tier=approved_tier,
        new_expiry=user.premium_expires_at,
        performed_by=request.user,
        reason=f'Approved request #{request_id}'
    )
    
    log_security_event(
        user=user,
        action='premium_approved',
        request=request,
        details={
            'approved_by': request.user.username,
            'approved_by_id': request.user.id,
            'request_id': request_id,
            'tier': approved_tier,
            'duration': approved_duration
        }
    )
    
    tier_benefits = {
        'basic': 'Access to all basic premium tools',
        'pro': 'Access to all premium tools + priority support',
        'enterprise': 'Full access + priority support + custom features'
    }
    
    duration_text = f'{approved_duration} days' if approved_duration > 0 else 'Lifetime'
    
    if premium_request.user.email:
        try:
            send_mail(
                'Premium Access Approved - VillenSec',
                f'''Congratulations {user.username}!

Your premium access request has been approved!

Plan Details:
- Tier: {approved_tier.upper()}
- Duration: {duration_text}
- Benefits: {tier_benefits.get(approved_tier, 'Full premium access')}

You now have access to all premium tools and features.

Thank you for being a VillenSec member!

Best regards,
VillenSec Team''',
                settings.DEFAULT_FROM_EMAIL,
                [premium_request.user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f'Failed to send approval email: {e}')
    
    messages.success(request, f"Premium {approved_tier.upper()} for {premium_request.user.username} approved ({duration_text}).")
    return redirect(reverse('tools:admin_dashboard'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_request(request, request_id):
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    
    if not premium_request.is_pending():
        messages.warning(request, f"Request is already {premium_request.get_status_display().lower()}.")
        return redirect(reverse('tools:admin_dashboard'))
    
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    
    premium_request.status = 'rejected'
    premium_request.reviewed_at = timezone.now()
    premium_request.reviewed_by = request.user
    if rejection_reason:
        premium_request.rejection_reason = rejection_reason
    premium_request.save()
    user = premium_request.user
    user.premium_request_status = 'rejected'
    user.save()
    
    log_security_event(
        user=user,
        action='premium_rejected',
        request=request,
        details={
            'rejected_by': request.user.username,
            'rejected_by_id': request.user.id,
            'request_id': request_id,
            'reason': rejection_reason
        }
    )
    
    if premium_request.user.email:
        try:
            reason_text = f"\n\nReason: {rejection_reason}\n" if rejection_reason else ""
            send_mail(
                'Premium Access Request Update - VillenSec',
                f'''Hello {user.username},

Your premium access request has been reviewed and unfortunately could not be approved at this time.{reason_text}
If you believe this was a mistake or have questions, please contact our support team.

Best regards,
VillenSec Team''',
                settings.DEFAULT_FROM_EMAIL,
                [premium_request.user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f'Failed to send rejection email: {e}')
    
    messages.success(request, f"Premium request for {premium_request.user.username} rejected.")
    return redirect(reverse('tools:admin_dashboard'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def revoke_premium(request, user_id):
    from core.models import PremiumHistory
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect(reverse('tools:admin_dashboard'))
    
    target_user = get_object_or_404(CustomUser, id=user_id)
    
    if not target_user.is_premium:
        messages.warning(request, f'{target_user.username} does not have premium access.')
        return redirect(reverse('tools:admin_dashboard'))
    
    revoke_reason = request.POST.get('revoke_reason', '').strip()
    
    previous_tier = target_user.premium_tier
    previous_expiry = target_user.premium_expires_at
    
    target_user.is_premium = False
    target_user.premium_request_status = 'revoked'
    target_user.premium_tier = 'none'
    target_user.premium_expires_at = None
    target_user.save()
    
    PremiumHistory.objects.create(
        user=target_user,
        action='revoked',
        previous_tier=previous_tier,
        new_tier='none',
        previous_expiry=previous_expiry,
        performed_by=request.user,
        reason=revoke_reason
    )
    
    log_security_event(
        user=target_user,
        action='premium_revoked',
        request=request,
        details={
            'revoked_by': request.user.username,
            'revoked_by_id': request.user.id,
            'previous_tier': previous_tier,
            'reason': revoke_reason
        }
    )
    
    if target_user.email:
        try:
            reason_text = f"\n\nReason: {revoke_reason}\n" if revoke_reason else ""
            send_mail(
                'Premium Access Revoked - VillenSec',
                f'''Hello {target_user.username},

Your premium access has been revoked.{reason_text}
If you believe this was a mistake or have questions, please contact our support team.

Best regards,
VillenSec Team''',
                settings.DEFAULT_FROM_EMAIL,
                [target_user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f'Failed to send revocation email: {e}')
    
    messages.success(request, f"Premium access for {target_user.username} has been revoked.")
    return redirect(reverse('tools:admin_dashboard'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def premium_users_list(request):
    premium_users = CustomUser.objects.filter(is_premium=True).order_by('-premium_activated_at')
    
    context = {
        'premium_users': premium_users,
    }
    return render(request, 'tools/admin_panel/premium_users.html', context)
