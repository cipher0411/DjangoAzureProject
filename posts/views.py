from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, CategoryForm

def post_list(request):
    """Display all published posts"""
    posts = Post.objects.filter(status='published').select_related('author', 'category')
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(summary__icontains=query) |
            Q(author__username__icontains=query)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    # Pagination
    paginator = Paginator(posts, 9)  # Show 9 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories with post counts
    categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
    }
    return render(request, 'posts/post_list.html', context)

def post_detail(request, year, month, day, slug):
    """Display a single post"""
    post = get_object_or_404(
        Post,
        slug=slug,
        published_at__year=year,
        published_at__month=month,
        published_at__day=day,
        status='published'
    )
    
    # Increment view count
    post.views += 1
    post.save(update_fields=['views'])
    
    # Get comments
    comments = post.comments.filter(is_active=True).select_related('author')
    
    # Comment form
    if request.user.is_authenticated:
        comment_form = CommentForm()
    else:
        comment_form = None
    
    # Get related posts (same category, excluding current post)
    related_posts = Post.objects.filter(
        category=post.category,
        status='published'
    ).exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'related_posts': related_posts,
    }
    return render(request, 'posts/post_detail.html', context)

@login_required
def post_create(request):
    """Create a new post"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.slug = slugify(post.title)
            
            # Check if slug exists and make it unique
            original_slug = post.slug
            counter = 1
            while Post.objects.filter(slug=post.slug).exists():
                post.slug = f"{original_slug}-{counter}"
                counter += 1
            
            if post.status == 'published':
                post.published_at = timezone.now()
            
            post.save()
            messages.success(request, 'Your post has been created successfully!')
            return redirect('posts:post_detail', 
                          year=post.published_at.year if post.published_at else post.created_at.year,
                          month=post.published_at.month if post.published_at else post.created_at.month,
                          day=post.published_at.day if post.published_at else post.created_at.day,
                          slug=post.slug)
    else:
        form = PostForm()
    
    return render(request, 'posts/post_form.html', {'form': form, 'action': 'Create'})

@login_required
def post_edit(request, pk):
    """Edit an existing post"""
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)
            
            # Only update slug if title changed
            if updated_post.title != post.title:
                updated_post.slug = slugify(updated_post.title)
                
                # Make slug unique
                original_slug = updated_post.slug
                counter = 1
                while Post.objects.filter(slug=updated_post.slug).exclude(id=post.id).exists():
                    updated_post.slug = f"{original_slug}-{counter}"
                    counter += 1
            
            # Update published_at if status changed to published
            if updated_post.status == 'published' and not post.published_at:
                updated_post.published_at = timezone.now()
            
            updated_post.save()
            messages.success(request, 'Your post has been updated successfully!')
            
            if updated_post.status == 'published':
                return redirect('posts:post_detail',
                              year=updated_post.published_at.year,
                              month=updated_post.published_at.month,
                              day=updated_post.published_at.day,
                              slug=updated_post.slug)
            else:
                return redirect('posts:my_posts')
    else:
        form = PostForm(instance=post)
    
    return render(request, 'posts/post_form.html', {'form': form, 'action': 'Edit'})

@login_required
def post_delete(request, pk):
    """Delete a post"""
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted successfully!')
        return redirect('posts:my_posts')
    
    return render(request, 'posts/post_confirm_delete.html', {'post': post})

@login_required
def my_posts(request):
    """Show posts by the current user"""
    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status in ['draft', 'published']:
        posts = posts.filter(status=status)
    
    context = {
        'posts': posts,
        'current_status': status,
    }
    return render(request, 'posts/my_posts.html', context)

@login_required
def add_comment(request, pk):
    """Add a comment to a post"""
    post = get_object_or_404(Post, pk=pk, status='published')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Your comment has been added!')
    
    return redirect('posts:post_detail', 
                   year=post.published_at.year,
                   month=post.published_at.month,
                   day=post.published_at.day,
                   slug=post.slug)

@login_required
def delete_comment(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    post = comment.post
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Your comment has been deleted.')
    
    return redirect('posts:post_detail',
                   year=post.published_at.year,
                   month=post.published_at.month,
                   day=post.published_at.day,
                   slug=post.slug)

@login_required
def like_post(request, pk):
    """Like or unlike a post"""
    post = get_object_or_404(Post, pk=pk, status='published')
    
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes()
        })
    
    return redirect('posts:post_detail',
                   year=post.published_at.year,
                   month=post.published_at.month,
                   day=post.published_at.day,
                   slug=post.slug)

def category_list(request):
    """Display all categories"""
    categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).order_by('name')
    
    return render(request, 'posts/category_list.html', {'categories': categories})

def category_posts(request, slug):
    """Display posts in a specific category"""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, status='published')
    
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'posts/category_posts.html', context)

@login_required
def category_create(request):
    """Create a new category (admin-like feature)"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to create categories.')
        return redirect('posts:post_list')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.slug = slugify(category.name)
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('posts:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'posts/category_form.html', {'form': form})