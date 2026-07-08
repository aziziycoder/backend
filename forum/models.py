from django.conf import settings
from django.db import models
from django.utils.text import slugify

from books.models import Book

User = settings.AUTH_USER_MODEL


class ForumThread(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(unique=True, blank=True, max_length=280)
    body = models.TextField()
    author = models.ForeignKey(User, related_name='threads', on_delete=models.CASCADE)
    # ixtiyoriy: mavzu muayyan kitobga bog'langan bo'lishi mumkin
    book = models.ForeignKey(
        Book, related_name='threads', on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_activity']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'thread'
            slug = base
            n = 1
            while ForumThread.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ForumPost(models.Model):
    thread = models.ForeignKey(ForumThread, related_name='posts', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='forum_posts', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author}: {self.text[:50]}'
