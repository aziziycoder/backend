from django.utils import timezone
from rest_framework import generics

from books.models import Book
from .models import ForumPost, ForumThread
from .serializers import (
    ForumPostSerializer,
    ThreadDetailSerializer,
    ThreadListSerializer,
)


class ThreadListCreateView(generics.ListCreateAPIView):
    serializer_class = ThreadListSerializer
    search_fields = ['title', 'body']

    def get_queryset(self):
        qs = ForumThread.objects.select_related('author', 'book__author').prefetch_related('posts')
        book_slug = self.request.query_params.get('book')
        if book_slug:
            qs = qs.filter(book__slug=book_slug)
        return qs

    def perform_create(self, serializer):
        book_slug = self.request.data.get('book')
        book = Book.objects.filter(slug=book_slug).first() if book_slug else None
        serializer.save(author=self.request.user, book=book)


class ThreadDetailView(generics.RetrieveAPIView):
    serializer_class = ThreadDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return ForumThread.objects.select_related('author', 'book__author').prefetch_related(
            'posts__author'
        )


class ThreadPostCreateView(generics.CreateAPIView):
    serializer_class = ForumPostSerializer

    def perform_create(self, serializer):
        thread = generics.get_object_or_404(ForumThread, slug=self.kwargs['slug'])
        serializer.save(author=self.request.user, thread=thread)
        thread.last_activity = timezone.now()
        thread.save(update_fields=['last_activity'])
