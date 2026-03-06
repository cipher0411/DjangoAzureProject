from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Post list and detail
    path('', views.post_list, name='post_list'),
    path('post/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.post_detail, name='post_detail'),
    
    # Post CRUD
    path('post/create/', views.post_create, name='post_create'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('my-posts/', views.my_posts, name='my_posts'),
    
    # Comments
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    
    # Likes
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
]