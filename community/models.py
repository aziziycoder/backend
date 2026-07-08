from django.conf import settings
from django.db import models

from books.models import Book

User = settings.AUTH_USER_MODEL


class Review(models.Model):
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    rating = models.FloatField()  # 0.5..5, 0.5 qadam bilan
    text = models.TextField(blank=True)
    has_spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.book} ({self.rating})'


class ReviewComment(models.Model):
    user = models.ForeignKey(User, related_name='review_comments', on_delete=models.CASCADE)
    review = models.ForeignKey(Review, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user}: {self.text[:50]}'


class ReviewLike(models.Model):
    user = models.ForeignKey(User, related_name='review_likes', on_delete=models.CASCADE)
    review = models.ForeignKey(Review, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f'{self.user} ♥ {self.review}'


class ShelfItem(models.Model):
    WANT = 'want'
    READING = 'reading'
    READ = 'read'
    STATUS_CHOICES = [(WANT, 'Want to read'), (READING, 'Reading'), (READ, 'Read')]

    user = models.ForeignKey(User, related_name='shelf', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='shelf_items', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    started_on = models.DateField(null=True, blank=True)  # "o'qiyapman" bosilgan kun
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user} - {self.book} [{self.status}]'


class Favorite(models.Model):
    user = models.ForeignKey(User, related_name='favorites', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='favorites', on_delete=models.CASCADE)
    # profilda "Sevimli kitoblar" sifatida ko'rsatiladigan tartib (0..3), null = ko'rsatilmaydi
    featured_order = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} ♥ {self.book}'


class DiaryEntry(models.Model):
    user = models.ForeignKey(User, related_name='diary_entries', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='diary_entries', on_delete=models.CASCADE)
    date_started = models.DateField(null=True, blank=True)
    date_read = models.DateField()
    rating = models.FloatField(null=True, blank=True)  # 0.5..5, 0.5 qadam
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_read', '-created_at']
        verbose_name_plural = 'diary entries'

    def __str__(self):
        return f'{self.user} - {self.book} ({self.date_read})'


class ReadingList(models.Model):
    user = models.ForeignKey(User, related_name='reading_lists', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.user})'


class ReadingListItem(models.Model):
    reading_list = models.ForeignKey(ReadingList, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='list_items', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reading_list', 'book')
        ordering = ['added_at']

    def __str__(self):
        return f'{self.reading_list.title}: {self.book.title}'


class ListLike(models.Model):
    user = models.ForeignKey(User, related_name='list_likes', on_delete=models.CASCADE)
    reading_list = models.ForeignKey(ReadingList, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'reading_list')

    def __str__(self):
        return f'{self.user} ♥ {self.reading_list}'


class ListComment(models.Model):
    user = models.ForeignKey(User, related_name='list_comments', on_delete=models.CASCADE)
    reading_list = models.ForeignKey(ReadingList, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user}: {self.text[:50]}'


class Question(models.Model):
    user = models.ForeignKey(User, related_name='questions', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.book}: {self.text[:50]}'


class Answer(models.Model):
    user = models.ForeignKey(User, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user}: {self.text[:50]}'


class Activity(models.Model):
    REVIEWED = 'reviewed'
    SHELVED_WANT = 'shelved_want'
    STARTED = 'started'
    FINISHED = 'finished'
    LOGGED = 'logged'
    VERB_CHOICES = [
        (REVIEWED, 'reviewed'),
        (SHELVED_WANT, 'shelved want'),
        (STARTED, 'started reading'),
        (FINISHED, 'finished reading'),
        (LOGGED, 'logged in diary'),
    ]

    user = models.ForeignKey(User, related_name='activities', on_delete=models.CASCADE)
    verb = models.CharField(max_length=20, choices=VERB_CHOICES)
    book = models.ForeignKey(Book, related_name='activities', on_delete=models.CASCADE)
    review = models.ForeignKey(Review, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'activities'

    def __str__(self):
        return f'{self.user} {self.verb} {self.book}'
