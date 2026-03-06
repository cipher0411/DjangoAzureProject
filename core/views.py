from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum

def home_view(request):
    context = {
        'total_users': User.objects.count(),
    }
    return render(request, 'core/home.html', context)

def about_view(request):
    return render(request, 'core/about.html')

@login_required
def dashboard_view(request):
    # Calculate total views for user's posts
    total_views = request.user.posts.aggregate(total=Sum('views'))['total'] or 0
    
    # Add manager methods for filtering posts
    # This adds the ability to use user.posts.published and user.posts.draft in template
    from posts.models import Post
    
    context = {
        'total_views': total_views,
    }
    return render(request, 'core/dashboard.html', context)