from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('home/', views.EventListView.as_view(), name='home'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('register/<int:event_id>/', views.register_for_event, name='register_for_event'),
    path('unregister/<int:event_id>/', views.unregister_from_event, name='unregister_from_event'),
    path('create/', views.create_event, name='create_event'),
    path('edit/<int:pk>/', views.edit_event, name='edit_event'),
    path('delete/<int:pk>/', views.delete_event, name='delete_event'),
]
