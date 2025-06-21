from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from .models import Service, BlogPost, UserProfile, ContactMessage
from .forms import ContactForm, UserProfileForm, BlogPostForm
from django import forms
import logging
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse


logger = logging.getLogger(__name__)

from tools.models import Tool

def home(request):
    tools = Tool.objects.all().order_by('-created_at')[:5]
    return render(request, 'core/home.html', {'tools': tools})


def about(request):
    return render(request, 'core/about.html')


from django.http import JsonResponse

def contact(request):
    """Contact form with AJAX and reCAPTCHA validation, logs email errors."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            try:
                send_mail(
                    f"New contact message: {contact_message.subject}",
                    f"From: {contact_message.name} <{contact_message.email}>\n\n{contact_message.message}",
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error('Email delivery failed: %s', str(e))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Your message has been sent successfully.'})
            else:
                messages.success(request, 'Your message has been sent successfully.')
                return redirect('core:home')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = form.errors.as_json()
                return JsonResponse({'success': False, 'message': 'There were errors in the form.', 'errors': errors})
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})

def is_superuser(user):
    return user.is_superuser

from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.is_superuser)
def blog_create(request):
    """Allow only superusers to create blog posts."""
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            blog_post.author = request.user
            blog_post.save()
            messages.success(request, 'Blog post created successfully.')
            return redirect('core:blog_list')
    else:
        form = BlogPostForm()
    return render(request, 'core/blog_form.html', {'form': form, 'title': 'Create Blog Post'})

@login_required
def blog_update(request, slug):
    """Allow only superusers or the author to edit blog posts."""
    blog_post = get_object_or_404(BlogPost, slug=slug)
    if request.user != blog_post.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('core:blog_detail', slug=slug)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, instance=blog_post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog post updated successfully.')
            return redirect('core:blog_detail', slug=slug)
    else:
        form = BlogPostForm(instance=blog_post)
    return render(request, 'core/blog_form.html', {'form': form, 'title': 'Edit Blog Post'})

@login_required
def blog_delete(request, slug):
    """Allow only superusers or the author to delete blog posts."""
    blog_post = get_object_or_404(BlogPost, slug=slug)
    if request.user != blog_post.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('core:blog_detail', slug=slug)
    if request.method == 'POST':
        blog_post.delete()
        messages.success(request, 'Blog post deleted successfully.')
        return redirect('core:blog_list')
    return render(request, 'core/confirm_delete.html', {'object': blog_post, 'title': 'Delete Blog Post'})

def register(request):
    """User registration with duplicate and password validation."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'A user with that username already exists.')
            else:
                user = form.save()
                messages.success(request, f'Account created for {username}. You can now log in.')
                return redirect('core:login')
        else:
            # Add custom error for weak passwords
            if 'password2' in form.errors:
                form.add_error('password2', 'Password is too weak or does not match.')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

from django.shortcuts import render
from .models import Service

def services_view(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    services = Service.objects.all()

    if query:
        services = services.filter(title__icontains=query)

    if category:
        services = services.filter(category=category)

    context = {
        'services': services,
        'query': query,
        'category': category,
        'categories': Service.CATEGORY_CHOICES,
    }
    return render(request, 'core/services.html', context)

def blog_list(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'core/blog_list.html', {'posts': posts})

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    return render(request, 'core/blog_detail.html', {'post': post})

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('core:profile')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'core/profile.html', {'form': form})

from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, 'core/404.html', status=404)

def custom_500_view(request):
    return render(request, 'core/500.html', status=500)
