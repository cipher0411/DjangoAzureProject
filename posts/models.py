from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='published')

class DraftManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='draft')

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('posts:category_posts', args=[self.slug])

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique_for_date='created_at')
    content = models.TextField()
    summary = models.TextField(max_length=300, help_text="Brief description of your post")
    featured_image = models.ImageField(upload_to='posts/', blank=True, null=True)
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    views = models.IntegerField(default=0)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Custom managers
    objects = models.Manager()  # The default manager
    published = PublishedManager()
    draft = DraftManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.status == 'published' and self.published_at:
            return reverse('posts:post_detail', args=[
                self.published_at.year,
                self.published_at.month,
                self.published_at.day,
                self.slug
            ])
        else:
            # For draft posts, you might want to go to edit page or list
            return reverse('posts:post_edit', args=[self.pk])

    def total_likes(self):
        return self.likes.count()

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'

    def total_likes(self):
        return self.likes.count()