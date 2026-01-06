from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('staff_directory/', views.StaffDirectoryView.as_view(), name='staff_directory'),
    path('contact/', views.contact_view, name='contact'),
    path('research-assistance/', views.research_assistance_view, name='research_assistance'),
    path('interlibrary-loan/', views.interlibrary_loan_view, name='interlibrary_loan'),
    path('study-room-booking/', views.study_room_booking_view, name='study_room_booking'),
    path('digital-resources/', views.digital_resources_view, name='digital_resources'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-use/', views.terms_of_use_view, name='terms_of_use'),
    path('tour/', views.virtual_tour_view, name='virtual_tour'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]
