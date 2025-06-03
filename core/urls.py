from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='core/logged_out.html', next_page='core:home'), name='logout'),
    path('services/', views.services_view, name='services'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/create/', views.blog_create, name='blog_create'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/<slug:slug>/edit/', views.blog_update, name='blog_update'),
    path('blog/<slug:slug>/delete/', views.blog_delete, name='blog_delete'),
    path('contact/', views.contact, name='contact'),
    path('profile/', views.profile, name='profile'),
    path('about/', views.about, name='about'),
]
