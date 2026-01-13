from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('execute-action/', views.execute_action, name='execute_action'),
    path('import-data/<str:app_label>/<str:model_name>/', views.import_data_view, name='import_data'),
    path('export-data/<str:app_label>/<str:model_name>/', views.export_data_view, name='export_data'),
    path('get-form/<str:app_label>/<str:model_name>/', views.get_form_view, name='get_form'),
    path('get-form/<str:app_label>/<str:model_name>/<int:item_id>/', views.get_form_view, name='get_form_edit'),
    path('approve-staff/<int:user_id>/', views.approve_staff, name='approve_staff'),
    path('reject-staff/<int:user_id>/', views.reject_staff, name='reject_staff'),
    path('user-role-management/', views.user_role_management, name='user_role_management'),
    path('change-user-role/<int:user_id>/', views.change_user_role, name='change_user_role'),
    path('delete/<str:app_label>/<str:model_name>/<int:item_id>/', views.delete_item, name='delete_item'),
    path('profile/', views.profile_view, name='profile'),
    path('staff_directory/', views.StaffDirectoryView.as_view(), name='staff_directory'),
    path('contact/', views.contact_view, name='contact'),
    path('research-assistance/', views.research_assistance_view, name='research_assistance'),
    path('interlibrary-loan/', views.interlibrary_loan_view, name='interlibrary_loan'),
    path('study-room-booking/', views.study_room_booking_view, name='study_room_booking'),
    path('digital-resources/', views.digital_resources_view, name='digital_resources'),
    path('library-resources/', views.library_resources_view, name='library_resources'),
    path('open-access/', views.open_access_view, name='open_access'),
    path('open-resources/', views.open_resources_view, name='open_resources'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-use/', views.terms_of_use_view, name='terms_of_use'),
    path('tour/', views.virtual_tour_view, name='virtual_tour'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),

    # QR code downloads
    path('users/<int:user_id>/qr/', views.download_user_qr, name='download_user_qr'),
]
