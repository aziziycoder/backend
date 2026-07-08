from django.db import models
from django.utils.text import slugify


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='authors/', blank=True, null=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, blank=True, max_length=320)
    author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE)
    genres = models.ManyToManyField(Genre, related_name='books', blank=True)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)
    cover_url = models.URLField(blank=True)  # tashqi muqova havolasi (seed uchun)
    published_year = models.PositiveIntegerField(null=True, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'book'
            slug = base
            n = 1
            while Book.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def cover_src(self):
        if self.cover:
            return self.cover.url
        return self.cover_url

    def __str__(self):
        return self.title


class Character(models.Model):
    book = models.ForeignKey(Book, related_name='characters', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    role = models.CharField(max_length=100, blank=True)  # masalan: bosh qahramon, antagonist

    def __str__(self):
        return f'{self.name} ({self.book.title})'
