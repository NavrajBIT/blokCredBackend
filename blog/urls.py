from django.urls import path
from . import views

urlpatterns = [
    path('api/login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/', views.list_users, name='list_users'),
    path('upload/', views.upload_image, name='upload-image'),
    path('delete/<int:pk>/', views.delete_image, name='delete-image'),
    path("posts/", views.list_posts, name="list_posts"),
    path('posts/<int:post_id>/', views.view_post, name='view_post'),
    path("posts/create/", views.create_post, name="create_post"),
    path('posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
]
