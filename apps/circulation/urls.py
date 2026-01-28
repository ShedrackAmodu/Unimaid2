from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    path('', views.circulation_home, name='circulation_home'),
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
    path('register-attendance/', views.register_attendance, name='register_attendance'),
    path('attendance-list/', views.attendance_list, name='attendance_list'),
    path('checkout-attendance/<int:attendance_id>/', views.checkout_attendance, name='checkout_attendance'),
    path('export-attendance-excel/', views.export_attendance_excel, name='export_attendance_excel'),
    
    # Study Room Booking URLs
    path('room-booking/', views.room_booking_view, name='room_booking'),
    path('room-calendar/', views.room_calendar_view, name='room_calendar'),
    path('approve-room-booking/<int:booking_id>/', views.approve_room_booking, name='approve_room_booking'),
    path('reject-room-booking/<int:booking_id>/', views.reject_room_booking, name='reject_room_booking'),
    path('cancel-room-booking/<int:booking_id>/', views.cancel_room_booking, name='cancel_room_booking'),
    path('my-room-bookings/', views.my_room_bookings, name='my_room_bookings'),
    path('cancel-my-room-booking/<int:booking_id>/', views.cancel_my_room_booking, name='cancel_my_room_booking'),
]
