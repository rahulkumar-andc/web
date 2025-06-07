from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.tools_list, name='tools_list'),
    path('tool/<int:pk>/', views.tool_detail, name='tool_detail'),
    path('request-premium/', views.request_premium, name='request_premium'),
    path('premium-request-status/', views.premium_request_status, name='premium_request_status'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
]
