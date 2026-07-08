from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import UserMiniSerializer
from .models import Author, Book, Genre
from .serializers import (
    AuthorDetailSerializer,
    AuthorSerializer,
    BookDetailSerializer,
    BookListSerializer,
    GenreSerializer,
)

User = get_user_model()


class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class BookListView(generics.ListAPIView):
    serializer_class = BookListSerializer
    search_fields = ['title', 'author__name']
    filterset_fields = {'genres__slug': ['exact'], 'published_year': ['exact', 'gte', 'lte']}
    ordering_fields = ['created_at', 'published_year', 'title']

    def get_queryset(self):
        qs = Book.objects.select_related('author').prefetch_related('genres')
        qs = qs.annotate(_avg=Avg('reviews__rating'), _cnt=Count('reviews'))
        ordering = self.request.query_params.get('ordering')
        if ordering == 'popular':
            qs = qs.order_by('-_cnt', '-_avg')
        elif ordering == 'top':
            qs = qs.order_by('-_avg', '-_cnt')
        return qs


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.select_related('author').prefetch_related('genres', 'characters')
    serializer_class = BookDetailSerializer
    lookup_field = 'slug'


class AuthorDetailView(generics.RetrieveAPIView):
    queryset = Author.objects.prefetch_related('books__genres', 'books__author')
    serializer_class = AuthorDetailSerializer


class SearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'books': [], 'authors': [], 'users': []})
        books = Book.objects.filter(
            Q(title__icontains=q) | Q(author__name__icontains=q)
        ).select_related('author').prefetch_related('genres')[:12]
        authors = Author.objects.filter(name__icontains=q)[:8]
        users = User.objects.filter(username__icontains=q, is_active=True)[:8]
        return Response({
            'books': BookListSerializer(books, many=True, context={'request': request}).data,
            'authors': AuthorSerializer(authors, many=True, context={'request': request}).data,
            'users': UserMiniSerializer(users, many=True, context={'request': request}).data,
        })
