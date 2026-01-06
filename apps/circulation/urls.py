from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('dashboard/', views.patron_dashboard, name='patron_dashboard'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('checkout/', views.checkout_book, name='checkout'),
    path('return/', views.return_book, name='return'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('cancel-request/<int:request_id>/', views.cancel_borrow_request, name='cancel_borrow_request'),
    path('approve-request/<int:request_id>/', views.approve_borrow_request, name='approve_borrow_request'),
    path('reject-request/<int:request_id>/', views.reject_borrow_request, name='reject_borrow_request'),
    path('renew/<int:loan_id>/', views.renew_loan, name='renew_loan'),
    path('pay-fine/<int:fine_id>/', views.pay_fine, name='pay_fine'),
]
