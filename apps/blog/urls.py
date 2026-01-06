from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogPostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', views.BlogPostDetailView.as_view(), name='post_detail'),
    path('create/', views.create_post, name='create_post'),
    path('edit/<int:pk>/', views.edit_post, name='edit_post'),
    path('delete/<int:pk>/', views.delete_post, name='delete_post'),
    path('publish/<int:pk>/', views.publish_post, name='publish_post'),
    path('drafts/', views.draft_posts, name='draft_posts'),
]
