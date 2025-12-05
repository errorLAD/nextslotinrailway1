"""
URL configuration for providers app.
"""
from django.urls import path
from . import views
from . import views_cbv
from . import views_analytics
from . import domain_views
from . import views_multi_domain

app_name = 'providers'

urlpatterns = [
    # Dashboard (Class-Based Views)
    path('dashboard/', views_cbv.DashboardView.as_view(), name='dashboard'),
    path('calendar/', views_cbv.CalendarView.as_view(), name='calendar'),
    path('api/appointments/', views_cbv.AppointmentsJSONView.as_view(), name='appointments_json'),
    
    # Profile Setup (Function-Based for initial setup)
    path('setup/', views.setup_profile, name='setup_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Services Management (Class-Based Views)
    path('services/', views_cbv.ServiceListView.as_view(), name='service_list'),
    path('services/add/', views_cbv.ServiceCreateView.as_view(), name='add_service'),
    path('services/<int:pk>/edit/', views_cbv.ServiceUpdateView.as_view(), name='edit_service'),
    path('services/<int:pk>/delete/', views_cbv.ServiceDeleteView.as_view(), name='delete_service'),
    
    # Availability Management removed
    
    # Custom Domain Management (Single Domain - Legacy)
    path('domain/', domain_views.custom_domain_page, name='custom_domain'),
    path('domain/settings/', domain_views.domain_settings, name='domain_settings'),
    path('domain/add/', domain_views.add_custom_domain, name='add_custom_domain'),
    path('domain/verify/', domain_views.domain_verification, name='domain_verification'),
    path('domain/verify/check/', domain_views.verify_domain, name='verify_domain'),
    path('domain/remove/', domain_views.remove_domain, name='remove_domain'),
    
    # Multi-Domain Management (NEW - PRO Feature)
    path('domains/', views_multi_domain.multi_domains_dashboard, name='multi_domains_dashboard'),
    path('domains/add/', views_multi_domain.add_domain, name='add_domain'),
    path('domains/<int:domain_id>/setup/', views_multi_domain.domain_setup, name='domain_setup'),
    path('domains/<int:domain_id>/verify/', views_multi_domain.domain_verify, name='domain_verify'),
    path('domains/<int:domain_id>/manage/', views_multi_domain.domain_manage, name='domain_manage'),
    path('domains/<int:domain_id>/set-primary/', views_multi_domain.set_primary, name='set_primary'),
    path('domains/<int:domain_id>/remove/', views_multi_domain.remove_domain, name='remove_domain'),
    path('domains/<int:domain_id>/status/', views_multi_domain.domain_status_json, name='domain_status_json'),
    path('domains/list/json/', views_multi_domain.domains_list_json, name='domains_list_json'),
    
    # Appointments (Class-Based Views)
    path('appointments/', views_cbv.AppointmentListView.as_view(), name='appointment_list'),
    path('appointments/create/', views_cbv.AppointmentCreateView.as_view(), name='create_appointment'),
    path('appointments/<int:pk>/', views_cbv.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('appointments/<int:pk>/edit/', views_cbv.AppointmentUpdateView.as_view(), name='edit_appointment'),
    
    # Appointment Actions (Function-Based for quick actions)
    path('appointments/<int:pk>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/<int:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    
    # Analytics (PRO feature with FREE teaser)
    path('analytics/', views_analytics.analytics_dashboard, name='analytics'),
    path('analytics/export/', views_analytics.export_analytics_csv, name='export_analytics'),
    path('analytics/api/', views_analytics.analytics_api, name='analytics_api'),
    
    # Billing & Subscription
    path('billing/', views_cbv.BillingView.as_view(), name='billing'),
    
    # Domain Management (PRO feature) - Legacy
    path('domains-legacy/', domain_views.domain_settings, name='domain_settings'),
    path('domains-legacy/add/', domain_views.add_custom_domain, name='add_custom_domain'),
    path('domains-legacy/verify/', domain_views.domain_verification, name='domain_verification'),
    path('domains-legacy/verify/check/', domain_views.verify_domain, name='verify_domain'),
    path('domains-legacy/remove/', domain_views.remove_domain, name='remove_domain'),
]
