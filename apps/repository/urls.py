from django.urls import path
from . import views

app_name = 'repository'

urlpatterns = [
    path('', views.EBookListView.as_view(), name='ebook_list'),
    path('ebook/<int:pk>/', views.EBookDetailView.as_view(), name='ebook_detail'),
    path('download/<int:pk>/', views.download_ebook, name='download_ebook'),
    path('upload/', views.upload_ebook, name='upload_ebook'),
    path('edit/<int:pk>/', views.edit_ebook, name='edit_ebook'),
    path('delete/<int:pk>/', views.delete_ebook, name='delete_ebook'),
    path('collections/', views.CollectionListView.as_view(), name='collection_list'),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection_detail'),

    # Permission request URLs
    path('ebook/<int:ebook_id>/request-permission/', views.request_ebook_permission, name='request_permission'),
    path('my-requests/', views.my_permission_requests, name='my_requests'),
    path('review-requests/', views.review_permission_requests, name='review_requests'),
    path('approve-request/<int:request_id>/', views.approve_permission_request, name='approve_request'),
    path('reject-request/<int:request_id>/', views.reject_permission_request, name='reject_request'),
]
