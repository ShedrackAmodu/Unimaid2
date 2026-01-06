from django.urls import path
from django.http import JsonResponse
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('books/', views.BookListView.as_view(), name='book_list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('authors/', views.AuthorListView.as_view(), name='author_list'),
    path('authors/<int:pk>/', views.AuthorDetailView.as_view(), name='author_detail'),
    path('publishers/', views.PublisherListView.as_view(), name='publisher_list'),
    path('publishers/<int:pk>/', views.PublisherDetailView.as_view(), name='publisher_detail'),
    path('faculties/', views.FacultyListView.as_view(), name='faculty_list'),
    path('faculties/<int:pk>/', views.FacultyDetailView.as_view(), name='faculty_detail'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('topics/', views.TopicListView.as_view(), name='topic_list'),
    path('topics/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('genres/', views.GenreListView.as_view(), name='genre_list'),
    path('genres/<int:pk>/', views.GenreDetailView.as_view(), name='genre_detail'),

    # Admin views
    path('admin/book/upload/', views.admin_book_upload, name='admin_book_upload'),
    path('admin/faculty/create/', views.admin_faculty_create, name='admin_faculty_create'),
    path('admin/department/create/', views.admin_department_create, name='admin_department_create'),
    path('admin/topic/create/', views.admin_topic_create, name='admin_topic_create'),

    # API endpoints for dynamic filtering
    path('api/departments/', views.api_departments, name='api_departments'),
    path('api/topics/', views.api_topics, name='api_topics'),

    # QR code downloads
    path('books/<int:book_id>/qr/', views.download_book_qr, name='download_book_qr'),
    path('copies/<int:copy_id>/qr/', views.download_copy_qr, name='download_copy_qr'),
]
