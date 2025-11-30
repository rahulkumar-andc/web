from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from core.models import (
    CustomUser, BlogPost, Service, ContactMessage, 
    SecurityLog, OTPAttemptLog, LoginAttemptLog, 
    UserSession, PremiumHistory, OTP, Note
)
from tools.models import Tool, PremiumRequest, ToolReview
from core.decorators import admin_required, moderator_required


@admin_required
def dashboard(request):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # 1. Basic Counts
    total_users = CustomUser.objects.count()
    new_users_today = CustomUser.objects.filter(date_joined__date=today).count()
    new_users_week = CustomUser.objects.filter(date_joined__gte=week_ago).count()
    
    premium_users = CustomUser.objects.filter(is_premium=True).count()
    pending_requests = PremiumRequest.objects.filter(status='pending').count()
    
    total_tools = Tool.objects.count()
    total_blogs = BlogPost.objects.count()
    
    # 2. Analytics Metrics
    
    # Daily Active Users (DAU) - Users active in last 24h
    dau_count = UserSession.objects.filter(last_activity__gte=now - timedelta(hours=24)).values('user').distinct().count()
    
    # Notes Downloads
    total_downloads = Note.objects.aggregate(total=Count('download_count'))['total'] or 0
    # Note: aggregate(Sum('download_count')) would be correct if download_count is a number, 
    # but since I just added it and it defaults to 0, Sum is better. 
    # Wait, I used Count above which counts rows. I need Sum.
    from django.db.models import Sum
    total_downloads = Note.objects.aggregate(total=Sum('download_count'))['total'] or 0

    # Tool Popularity (Top 5 by views - assuming we track views, if not use reviews count or random for now)
    # Since we don't have view count on Tool, let's use review count or just list them
    # For now, let's assume we want to show tools with most reviews
    popular_tools = Tool.objects.annotate(review_count=Count('reviews')).order_by('-review_count')[:5]
    
    # Premium Revenue (Estimated)
    # Basic=$10, Pro=$20, Enterprise=$50
    revenue_data = PremiumHistory.objects.filter(action='activated', created_at__gte=month_ago)
    estimated_revenue = 0
    for history in revenue_data:
        if history.new_tier == 'basic':
            estimated_revenue += 10
        elif history.new_tier == 'pro':
            estimated_revenue += 20
        elif history.new_tier == 'enterprise':
            estimated_revenue += 50
            
    # Failed Login Attempts (Last 7 Days Chart)
    failed_logins_chart = []
    for i in range(7):
        day = today - timedelta(days=i)
        count = LoginAttemptLog.objects.filter(
            was_successful=False, 
            attempted_at__date=day
        ).count()
        failed_logins_chart.append({'day': day.strftime('%a'), 'count': count})
    failed_logins_chart.reverse()
    
    # Device Map Data (Unique IPs from active sessions)
    active_ips = UserSession.objects.filter(last_activity__gte=week_ago).values_list('ip_address', flat=True).distinct()
    # We will pass these IPs to the template, and JS will fetch Geo location
    map_ips = list(active_ips)[:50] # Limit to 50 for performance
    
    # Recent Data
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    recent_requests = PremiumRequest.objects.filter(status='pending').order_by('-requested_at')[:5]
    recent_logs = SecurityLog.objects.order_by('-created_at')[:10]
    unread_messages = ContactMessage.objects.order_by('-created_at')[:5]
    
    # User Registrations Chart
    user_registrations_week = []
    for i in range(7):
        day = today - timedelta(days=i)
        count = CustomUser.objects.filter(date_joined__date=day).count()
        user_registrations_week.append({'day': day.strftime('%a'), 'count': count})
    user_registrations_week.reverse()
    
    context = {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'premium_users': premium_users,
        'pending_requests': pending_requests,
        'total_tools': total_tools,
        'total_blogs': total_blogs,
        'recent_users': recent_users,
        'recent_requests': recent_requests,
        'recent_logs': recent_logs,
        'unread_messages': unread_messages,
        'user_registrations_week': user_registrations_week,
        
        # New Analytics
        'dau_count': dau_count,
        'total_downloads': total_downloads,
        'popular_tools': popular_tools,
        'estimated_revenue': estimated_revenue,
        'failed_logins_chart': failed_logins_chart,
        'map_ips': map_ips,
    }
    return render(request, 'custom_admin/dashboard.html', context)


@admin_required
def analytics_api(request):
    """
    API endpoint for real-time dashboard updates.
    """
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    
    # Basic Counts
    total_users = CustomUser.objects.count()
    dau_count = UserSession.objects.filter(last_activity__gte=now - timedelta(hours=24)).values('user').distinct().count()
    total_downloads = Note.objects.aggregate(total=Count('download_count'))['total'] or 0
    
    # Failed Logins Chart Data
    failed_logins_chart = []
    for i in range(7):
        day = today - timedelta(days=i)
        count = LoginAttemptLog.objects.filter(
            was_successful=False, 
            attempted_at__date=day
        ).count()
        failed_logins_chart.append({'day': day.strftime('%a'), 'count': count})
    failed_logins_chart.reverse()
    
    data = {
        'total_users': total_users,
        'dau_count': dau_count,
        'total_downloads': total_downloads,
        'failed_logins_chart': failed_logins_chart,
    }
    return JsonResponse(data)


@admin_required
def user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'premium':
        users = users.filter(is_premium=True)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)
    
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'custom_admin/users/list.html', context)


@admin_required
def user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    security_logs = SecurityLog.objects.filter(user=user).order_by('-created_at')[:20]
    sessions = UserSession.objects.filter(user=user).order_by('-last_activity')
    premium_history = PremiumHistory.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'user_obj': user,
        'security_logs': security_logs,
        'sessions': sessions,
        'premium_history': premium_history,
    }
    return render(request, 'custom_admin/users/detail.html', context)


@admin_required
def user_edit(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.bio = request.POST.get('bio', '')
        user.phone_number = request.POST.get('phone_number', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.email_verified = request.POST.get('email_verified') == 'on'
        user.save()
        messages.success(request, f'User {user.username} updated successfully.')
        return redirect('custom_admin:user_detail', user_id=user.id)
    
    context = {'user_obj': user}
    return render(request, 'custom_admin/users/edit.html', context)


@admin_required
def user_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('custom_admin:user_list')
    
    context = {'user_obj': user}
    return render(request, 'custom_admin/users/delete.html', context)


@admin_required
def user_toggle_active(request, user_id):
    if request.method != 'POST':
        return redirect('custom_admin:user_list')
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} {status}.')
    return redirect('custom_admin:user_list')


@admin_required
def user_toggle_staff(request, user_id):
    if request.method != 'POST':
        return redirect('custom_admin:user_list')
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_staff = not user.is_staff
    user.save()
    status = 'given staff access' if user.is_staff else 'removed from staff'
    messages.success(request, f'User {user.username} {status}.')
    return redirect('custom_admin:user_list')


@admin_required
def premium_dashboard(request):
    pending_count = PremiumRequest.objects.filter(status='pending').count()
    approved_count = PremiumRequest.objects.filter(status='approved').count()
    rejected_count = PremiumRequest.objects.filter(status='rejected').count()
    
    premium_users = CustomUser.objects.filter(is_premium=True).count()
    basic_tier = CustomUser.objects.filter(is_premium=True, premium_tier='basic').count()
    pro_tier = CustomUser.objects.filter(is_premium=True, premium_tier='pro').count()
    enterprise_tier = CustomUser.objects.filter(is_premium=True, premium_tier='enterprise').count()
    
    recent_requests = PremiumRequest.objects.filter(status='pending').order_by('-requested_at')[:10]
    
    context = {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'premium_users': premium_users,
        'basic_tier': basic_tier,
        'pro_tier': pro_tier,
        'enterprise_tier': enterprise_tier,
        'recent_requests': recent_requests,
    }
    return render(request, 'custom_admin/premium/dashboard.html', context)


@moderator_required
def premium_requests(request):
    requests_qs = PremiumRequest.objects.all().order_by('-requested_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    
    paginator = Paginator(requests_qs, 20)
    page = request.GET.get('page', 1)
    requests_list = paginator.get_page(page)
    
    context = {
        'requests': requests_list,
        'status_filter': status_filter,
    }
    return render(request, 'custom_admin/premium/requests.html', context)


@admin_required
def approve_premium(request, request_id):
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    
    if request.method == 'POST':
        tier = request.POST.get('tier', 'basic')
        duration = int(request.POST.get('duration', 30))
        admin_notes = request.POST.get('admin_notes', '')
        
        premium_request.status = 'approved'
        premium_request.approved_tier = tier
        premium_request.approved_duration = duration
        premium_request.admin_notes = admin_notes
        premium_request.reviewed_at = timezone.now()
        premium_request.reviewed_by = request.user
        premium_request.save()
        
        user = premium_request.user
        user.is_premium = True
        user.premium_tier = tier
        user.premium_request_status = 'approved'
        user.premium_activated_at = timezone.now()
        
        if duration > 0:
            user.premium_expires_at = timezone.now() + timedelta(days=duration)
        else:
            user.premium_expires_at = None
        user.save()
        
        PremiumHistory.objects.create(
            user=user,
            action='activated',
            new_tier=tier,
            new_expiry=user.premium_expires_at,
            performed_by=request.user,
            reason=f'Premium request approved'
        )
        
        messages.success(request, f'Premium request for {user.username} approved.')
        return redirect('custom_admin:premium_requests')
    
    context = {'premium_request': premium_request}
    return render(request, 'custom_admin/premium/approve.html', context)


@admin_required
def reject_premium(request, request_id):
    premium_request = get_object_or_404(PremiumRequest, id=request_id)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        admin_notes = request.POST.get('admin_notes', '')
        
        premium_request.status = 'rejected'
        premium_request.rejection_reason = rejection_reason
        premium_request.admin_notes = admin_notes
        premium_request.reviewed_at = timezone.now()
        premium_request.reviewed_by = request.user
        premium_request.save()
        
        user = premium_request.user
        user.premium_request_status = 'rejected'
        user.save()
        
        messages.success(request, f'Premium request for {user.username} rejected.')
        return redirect('custom_admin:premium_requests')
    
    context = {'premium_request': premium_request}
    return render(request, 'custom_admin/premium/reject.html', context)


@admin_required
def premium_users(request):
    users = CustomUser.objects.filter(is_premium=True).order_by('-premium_activated_at')
    
    tier_filter = request.GET.get('tier', '')
    if tier_filter:
        users = users.filter(premium_tier=tier_filter)
    
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'tier_filter': tier_filter,
    }
    return render(request, 'custom_admin/premium/users.html', context)


@admin_required
def revoke_premium(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        old_tier = user.premium_tier
        old_expiry = user.premium_expires_at
        
        user.is_premium = False
        user.premium_tier = 'none'
        user.premium_request_status = 'revoked'
        user.premium_expires_at = None
        user.save()
        
        PremiumHistory.objects.create(
            user=user,
            action='revoked',
            previous_tier=old_tier,
            new_tier='none',
            previous_expiry=old_expiry,
            performed_by=request.user,
            reason=reason
        )
        
        messages.success(request, f'Premium access revoked for {user.username}.')
        return redirect('custom_admin:premium_users')
    
    context = {'user_obj': user}
    return render(request, 'custom_admin/premium/revoke.html', context)


@admin_required
def extend_premium(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        days = int(request.POST.get('days', 30))
        reason = request.POST.get('reason', '')
        
        old_expiry = user.premium_expires_at
        
        if user.premium_expires_at:
            user.premium_expires_at = user.premium_expires_at + timedelta(days=days)
        else:
            user.premium_expires_at = timezone.now() + timedelta(days=days)
        user.save()
        
        PremiumHistory.objects.create(
            user=user,
            action='extended',
            previous_expiry=old_expiry,
            new_expiry=user.premium_expires_at,
            performed_by=request.user,
            reason=reason
        )
        
        messages.success(request, f'Premium extended for {user.username} by {days} days.')
        return redirect('custom_admin:premium_users')
    
    context = {'user_obj': user}
    return render(request, 'custom_admin/premium/extend.html', context)


@moderator_required
def tools_list(request):
    tools = Tool.objects.all().order_by('-created_at')
    
    search = request.GET.get('search', '')
    if search:
        tools = tools.filter(
            Q(title__icontains=search) |
            Q(category__icontains=search)
        )
    
    category = request.GET.get('category', '')
    if category:
        tools = tools.filter(category=category)
    
    categories = Tool.objects.values_list('category', flat=True).distinct()
    
    paginator = Paginator(tools, 20)
    page = request.GET.get('page', 1)
    tools = paginator.get_page(page)
    
    context = {
        'tools': tools,
        'search': search,
        'category': category,
        'categories': categories,
    }
    return render(request, 'custom_admin/tools/list.html', context)


@admin_required
def tool_create(request):
    if request.method == 'POST':
        tool = Tool(
            title=request.POST.get('title', ''),
            category=request.POST.get('category', 'General'),
            image_url=request.POST.get('image_url', ''),
            video_url=request.POST.get('video_url', ''),
            source_code_url=request.POST.get('source_code_url', ''),
            detailed_content=request.POST.get('detailed_content', ''),
            author=request.user
        )
        tool.save()
        messages.success(request, f'Tool "{tool.title}" created successfully.')
        return redirect('custom_admin:tools_list')
    
    return render(request, 'custom_admin/tools/create.html')


@admin_required
def tool_edit(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    
    if request.method == 'POST':
        tool.title = request.POST.get('title', '')
        tool.category = request.POST.get('category', 'General')
        tool.image_url = request.POST.get('image_url', '')
        tool.video_url = request.POST.get('video_url', '')
        tool.source_code_url = request.POST.get('source_code_url', '')
        tool.detailed_content = request.POST.get('detailed_content', '')
        tool.save()
        messages.success(request, f'Tool "{tool.title}" updated successfully.')
        return redirect('custom_admin:tools_list')
    
    context = {'tool': tool}
    return render(request, 'custom_admin/tools/edit.html', context)


@admin_required
def tool_delete(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        title = tool.title
        tool.delete()
        messages.success(request, f'Tool "{title}" deleted successfully.')
        return redirect('custom_admin:tools_list')
    
    context = {'tool': tool}
    return render(request, 'custom_admin/tools/delete.html', context)


@admin_required
def blog_list(request):
    blogs = BlogPost.objects.all().order_by('-created_at')
    
    search = request.GET.get('search', '')
    if search:
        blogs = blogs.filter(
            Q(title__icontains=search) |
            Q(author__username__icontains=search)
        )
    
    paginator = Paginator(blogs, 20)
    page = request.GET.get('page', 1)
    blogs = paginator.get_page(page)
    
    context = {
        'blogs': blogs,
        'search': search,
    }
    return render(request, 'custom_admin/blogs/list.html', context)


@admin_required
def blog_create(request):
    if request.method == 'POST':
        blog = BlogPost(
            title=request.POST.get('title', ''),
            content=request.POST.get('content', ''),
            image_url=request.POST.get('image_url', ''),
            is_private=request.POST.get('is_private') == 'on',
            author=request.user
        )
        blog.save()
        messages.success(request, f'Blog "{blog.title}" created successfully.')
        return redirect('custom_admin:blog_list')
    
    return render(request, 'custom_admin/blogs/create.html')


@admin_required
def blog_edit(request, blog_id):
    blog = get_object_or_404(BlogPost, id=blog_id)
    
    if request.method == 'POST':
        blog.title = request.POST.get('title', '')
        blog.content = request.POST.get('content', '')
        blog.image_url = request.POST.get('image_url', '')
        blog.is_private = request.POST.get('is_private') == 'on'
        blog.save()
        messages.success(request, f'Blog "{blog.title}" updated successfully.')
        return redirect('custom_admin:blog_list')
    
    context = {'blog': blog}
    return render(request, 'custom_admin/blogs/edit.html', context)


@admin_required
def blog_delete(request, blog_id):
    blog = get_object_or_404(BlogPost, id=blog_id)
    if request.method == 'POST':
        title = blog.title
        blog.delete()
        messages.success(request, f'Blog "{title}" deleted successfully.')
        return redirect('custom_admin:blog_list')
    
    context = {'blog': blog}
    return render(request, 'custom_admin/blogs/delete.html', context)


@admin_required
def security_dashboard(request):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    
    total_logs = SecurityLog.objects.count()
    today_logs = SecurityLog.objects.filter(created_at__date=today).count()
    
    failed_logins = LoginAttemptLog.objects.filter(was_successful=False, attempted_at__gte=week_ago).count()
    successful_logins = LoginAttemptLog.objects.filter(was_successful=True, attempted_at__gte=week_ago).count()
    
    suspicious_logs = SecurityLog.objects.filter(action='suspicious_activity', created_at__gte=week_ago).count()
    
    active_sessions = UserSession.objects.count()
    
    recent_logs = SecurityLog.objects.order_by('-created_at')[:10]
    recent_failed_logins = LoginAttemptLog.objects.filter(was_successful=False).order_by('-attempted_at')[:10]
    
    context = {
        'total_logs': total_logs,
        'today_logs': today_logs,
        'failed_logins': failed_logins,
        'successful_logins': successful_logins,
        'suspicious_logs': suspicious_logs,
        'active_sessions': active_sessions,
        'recent_logs': recent_logs,
        'recent_failed_logins': recent_failed_logins,
    }
    return render(request, 'custom_admin/security/dashboard.html', context)


@admin_required
def security_logs(request):
    logs = SecurityLog.objects.all().order_by('-created_at')
    
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    search = request.GET.get('search', '')
    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    action_choices = SecurityLog.ACTION_CHOICES
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs = paginator.get_page(page)
    
    context = {
        'logs': logs,
        'action_filter': action_filter,
        'search': search,
        'action_choices': action_choices,
    }
    return render(request, 'custom_admin/security/logs.html', context)


@admin_required
def login_attempts(request):
    attempts = LoginAttemptLog.objects.all().order_by('-attempted_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'success':
        attempts = attempts.filter(was_successful=True)
    elif status_filter == 'failed':
        attempts = attempts.filter(was_successful=False)
    
    paginator = Paginator(attempts, 50)
    page = request.GET.get('page', 1)
    attempts = paginator.get_page(page)
    
    context = {
        'attempts': attempts,
        'status_filter': status_filter,
    }
    return render(request, 'custom_admin/security/login_attempts.html', context)


@admin_required
def otp_attempts(request):
    attempts = OTPAttemptLog.objects.all().order_by('-attempted_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'success':
        attempts = attempts.filter(was_successful=True)
    elif status_filter == 'failed':
        attempts = attempts.filter(was_successful=False)
    
    paginator = Paginator(attempts, 50)
    page = request.GET.get('page', 1)
    attempts = paginator.get_page(page)
    
    context = {
        'attempts': attempts,
        'status_filter': status_filter,
    }
    return render(request, 'custom_admin/security/otp_attempts.html', context)


@admin_required
def active_sessions(request):
    sessions = UserSession.objects.all().order_by('-last_activity')
    
    search = request.GET.get('search', '')
    if search:
        sessions = sessions.filter(
            Q(user__username__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    paginator = Paginator(sessions, 50)
    page = request.GET.get('page', 1)
    sessions = paginator.get_page(page)
    
    context = {
        'sessions': sessions,
        'search': search,
    }
    return render(request, 'custom_admin/security/sessions.html', context)


@admin_required
def terminate_session(request, session_id):
    session = get_object_or_404(UserSession, id=session_id)
    if request.method == 'POST':
        username = session.user.username
        session.delete()
        messages.success(request, f'Session for {username} terminated.')
    return redirect('custom_admin:active_sessions')


@admin_required
def contact_messages(request):
    msgs = ContactMessage.objects.all().order_by('-created_at')
    
    search = request.GET.get('search', '')
    if search:
        msgs = msgs.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(subject__icontains=search)
        )
    
    paginator = Paginator(msgs, 20)
    page = request.GET.get('page', 1)
    msgs = paginator.get_page(page)
    
    context = {
        'messages_list': msgs,
        'search': search,
    }
    return render(request, 'custom_admin/messages/list.html', context)


@admin_required
def message_detail(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    context = {'msg': msg}
    return render(request, 'custom_admin/messages/detail.html', context)


@admin_required
def message_delete(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    if request.method == 'POST':
        msg.delete()
        messages.success(request, 'Message deleted successfully.')
        return redirect('custom_admin:contact_messages')
    
    context = {'msg': msg}
    return render(request, 'custom_admin/messages/delete.html', context)


@admin_required
def services_list(request):
    services = Service.objects.all().order_by('-id')
    
    category = request.GET.get('category', '')
    if category:
        services = services.filter(category=category)
    
    paginator = Paginator(services, 20)
    page = request.GET.get('page', 1)
    services = paginator.get_page(page)
    
    context = {
        'services': services,
        'category': category,
        'category_choices': Service.CATEGORY_CHOICES,
    }
    return render(request, 'custom_admin/services/list.html', context)


@admin_required
def service_create(request):
    if request.method == 'POST':
        service = Service(
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            icon=request.POST.get('icon', ''),
            image_url=request.POST.get('image_url', ''),
            category=request.POST.get('category', 'web')
        )
        service.save()
        messages.success(request, f'Service "{service.title}" created successfully.')
        return redirect('custom_admin:services_list')
    
    context = {'category_choices': Service.CATEGORY_CHOICES}
    return render(request, 'custom_admin/services/create.html', context)


@admin_required
def service_edit(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        service.title = request.POST.get('title', '')
        service.description = request.POST.get('description', '')
        service.icon = request.POST.get('icon', '')
        service.image_url = request.POST.get('image_url', '')
        service.category = request.POST.get('category', 'web')
        service.save()
        messages.success(request, f'Service "{service.title}" updated successfully.')
        return redirect('custom_admin:services_list')
    
    context = {
        'service': service,
        'category_choices': Service.CATEGORY_CHOICES,
    }
    return render(request, 'custom_admin/services/edit.html', context)


@admin_required
def service_delete(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        title = service.title
        service.delete()
        messages.success(request, f'Service "{title}" deleted successfully.')
        return redirect('custom_admin:services_list')
    
    context = {'service': service}
    return render(request, 'custom_admin/services/delete.html', context)


@admin_required
def api_stats(request):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    
    data = {
        'total_users': CustomUser.objects.count(),
        'new_users_today': CustomUser.objects.filter(date_joined__date=today).count(),
        'premium_users': CustomUser.objects.filter(is_premium=True).count(),
        'pending_requests': PremiumRequest.objects.filter(status='pending').count(),
        'total_tools': Tool.objects.count(),
        'total_blogs': BlogPost.objects.count(),
        'active_sessions': UserSession.objects.count(),
        'failed_logins_week': LoginAttemptLog.objects.filter(was_successful=False, attempted_at__gte=week_ago).count(),
    }
    return JsonResponse(data)
