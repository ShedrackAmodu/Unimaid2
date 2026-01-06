from django.urls import path
from . import views

app_name = 'repository'

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('document/<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('download/<int:pk>/', views.download_document, name='download_document'),
    path('upload/', views.upload_document, name='upload_document'),
    path('edit/<int:pk>/', views.edit_document, name='edit_document'),
    path('delete/<int:pk>/', views.delete_document, name='delete_document'),
    path('collections/', views.CollectionListView.as_view(), name='collection_list'),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection_detail'),
]
