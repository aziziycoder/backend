from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from users.models import Follow
from .models import (
    Activity,
    Answer,
    DiaryEntry,
    Favorite,
    ListLike,
    Question,
    ReadingList,
    ReadingListItem,
    Review,
    ReviewLike,
    ShelfItem,
)
from .serializers import (
    ActivitySerializer,
    AnswerSerializer,
    DiaryEntrySerializer,
    ListCommentSerializer,
    QuestionSerializer,
    ReadingListDetailSerializer,
    ReadingListSerializer,
    ReviewCommentSerializer,
    ReviewSerializer,
    ShelfItemSerializer,
)

User = get_user_model()


class BookReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_book(self):
        return generics.get_object_or_404(Book, slug=self.kwargs['slug'])

    def get_queryset(self):
        return Review.objects.filter(book=self.get_book()).select_related('user', 'book__author')

    def perform_create(self, serializer):
        book = self.get_book()
        # bitta foydalanuvchi bitta kitobga bitta taqriz — bor bo'lsa yangilanadi
        existing = Review.objects.filter(user=self.request.user, book=book).first()
        if existing:
            existing.rating = serializer.validated_data['rating']
            existing.text = serializer.validated_data.get('text', existing.text)
            existing.has_spoiler = serializer.validated_data.get('has_spoiler', existing.has_spoiler)
            existing.save()
            serializer.instance = existing
        else:
            review = serializer.save(user=self.request.user, book=book)
            Activity.objects.create(
                user=self.request.user, verb=Activity.REVIEWED, book=book, review=review
            )


class RecentReviewsView(generics.ListAPIView):
    queryset = Review.objects.select_related('user', 'book__author').exclude(text='')
    serializer_class = ReviewSerializer


class ReviewCommentCreateView(generics.CreateAPIView):
    serializer_class = ReviewCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        review = generics.get_object_or_404(Review, pk=self.kwargs['pk'])
        serializer.save(user=self.request.user, review=review)


class ReviewLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        review = generics.get_object_or_404(Review, pk=pk)
        like, created = ReviewLike.objects.get_or_create(user=request.user, review=review)
        if not created:
            like.delete()
        return Response({'liked': created, 'likes_count': review.likes.count()})


class ShelfView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        book = generics.get_object_or_404(Book, slug=slug)
        new_status = request.data.get('status')
        if new_status not in (ShelfItem.WANT, ShelfItem.READING, ShelfItem.READ):
            return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
        item, _ = ShelfItem.objects.update_or_create(
            user=request.user, book=book, defaults={'status': new_status}
        )
        # "o'qiyapman" bosilgan kun — kundalik uchun boshlanish sanasi
        if new_status == ShelfItem.READING and not item.started_on:
            from django.utils import timezone

            item.started_on = timezone.localdate()
            item.save()
        verb = {
            ShelfItem.WANT: Activity.SHELVED_WANT,
            ShelfItem.READING: Activity.STARTED,
            ShelfItem.READ: Activity.FINISHED,
        }[new_status]
        Activity.objects.create(user=request.user, verb=verb, book=book)
        return Response({'status': item.status})

    def delete(self, request, slug):
        ShelfItem.objects.filter(user=request.user, book__slug=slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserShelfView(generics.ListAPIView):
    serializer_class = ShelfItemSerializer

    def get_queryset(self):
        qs = ShelfItem.objects.filter(user__username=self.kwargs['username'])
        shelf_status = self.request.query_params.get('status')
        if shelf_status:
            qs = qs.filter(status=shelf_status)
        return qs.select_related('book__author')


class UserReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(user__username=self.kwargs['username']).select_related(
            'user', 'book__author'
        )


class BookDiaryCreateView(generics.CreateAPIView):
    serializer_class = DiaryEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        book = generics.get_object_or_404(Book, slug=self.kwargs['slug'])
        entry = serializer.save(user=self.request.user, book=book)
        # boshlanish sanasi berilmagan bo'lsa, "o'qiyapman" bosilgan kundan olinadi
        shelf_item = ShelfItem.objects.filter(user=self.request.user, book=book).first()
        if not entry.date_started and shelf_item and shelf_item.started_on:
            entry.date_started = shelf_item.started_on
            entry.save()
        # kundalikka yozilgan kitob avtomatik "o'qidim" ro'yxatiga tushadi
        ShelfItem.objects.update_or_create(
            user=self.request.user, book=book, defaults={'status': ShelfItem.READ}
        )
        Activity.objects.create(user=self.request.user, verb=Activity.LOGGED, book=book)
        return entry


class DiaryEntryDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DiaryEntry.objects.filter(user=self.request.user)


class UserDiaryView(generics.ListAPIView):
    serializer_class = DiaryEntrySerializer

    def get_queryset(self):
        return DiaryEntry.objects.filter(user__username=self.kwargs['username']).select_related(
            'user', 'book__author'
        )


class FriendsDiaryView(generics.ListAPIView):
    serializer_class = DiaryEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        following_ids = Follow.objects.filter(follower=self.request.user).values_list(
            'following_id', flat=True
        )
        return DiaryEntry.objects.filter(user_id__in=following_ids).select_related(
            'user', 'book__author'
        )


class ReadingListListCreateView(generics.ListCreateAPIView):
    serializer_class = ReadingListSerializer

    def get_queryset(self):
        qs = ReadingList.objects.select_related('user')
        if self.request.query_params.get('mine') and self.request.user.is_authenticated:
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReadingListDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ReadingListDetailSerializer
    queryset = ReadingList.objects.select_related('user')

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied()
        instance.delete()


class ReadingListBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reading_list = generics.get_object_or_404(ReadingList, pk=pk, user=request.user)
        book = generics.get_object_or_404(Book, slug=request.data.get('slug'))
        _, created = ReadingListItem.objects.get_or_create(reading_list=reading_list, book=book)
        return Response({'added': created, 'books_count': reading_list.items.count()})

    def delete(self, request, pk, slug=None):
        reading_list = generics.get_object_or_404(ReadingList, pk=pk, user=request.user)
        ReadingListItem.objects.filter(reading_list=reading_list, book__slug=slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reading_list = generics.get_object_or_404(ReadingList, pk=pk)
        like, created = ListLike.objects.get_or_create(user=request.user, reading_list=reading_list)
        if not created:
            like.delete()
        return Response({'liked': created, 'likes_count': reading_list.likes.count()})


class ListCommentCreateView(generics.CreateAPIView):
    serializer_class = ListCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        reading_list = generics.get_object_or_404(ReadingList, pk=self.kwargs['pk'])
        serializer.save(user=self.request.user, reading_list=reading_list)


class BookFavoriteToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        book = generics.get_object_or_404(Book, slug=slug)
        fav, created = Favorite.objects.get_or_create(user=request.user, book=book)
        if not created:
            fav.delete()
        return Response({'favorited': created, 'favorites_count': book.favorites.count()})


class UserFavoritesView(generics.ListAPIView):
    def get_serializer_class(self):
        from books.serializers import BookListSerializer

        return BookListSerializer

    def get_queryset(self):
        return Book.objects.filter(
            favorites__user__username=self.kwargs['username']
        ).select_related('author').prefetch_related('genres').order_by('-favorites__created_at')


class UserFeaturedView(generics.ListAPIView):
    """Profilda ko'rsatiladigan 4 tagacha sevimli kitob (tanlanmagan bo'lsa — oxirgi 4 ta)."""
    pagination_class = None

    def get_serializer_class(self):
        from books.serializers import BookListSerializer

        return BookListSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        featured = (
            Book.objects.filter(
                favorites__user__username=username,
                favorites__featured_order__isnull=False,
            )
            .select_related('author')
            .prefetch_related('genres')
            .order_by('favorites__featured_order')
        )
        if featured.exists():
            return featured
        return (
            Book.objects.filter(favorites__user__username=username)
            .select_related('author')
            .prefetch_related('genres')
            .order_by('-favorites__created_at')[:4]
        )


class MyFeaturedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        slugs = request.data.get('slugs', [])[:4]
        # avvalgi tanlovni tozalash
        Favorite.objects.filter(user=request.user).update(featured_order=None)
        for i, slug in enumerate(slugs):
            book = Book.objects.filter(slug=slug).first()
            if book:
                fav, _ = Favorite.objects.get_or_create(user=request.user, book=book)
                fav.featured_order = i
                fav.save()
        return Response({'count': len([s for s in slugs if Book.objects.filter(slug=s).exists()])})


class UserListsView(generics.ListAPIView):
    serializer_class = ReadingListSerializer

    def get_queryset(self):
        return ReadingList.objects.filter(user__username=self.kwargs['username']).select_related('user')


class BookQuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return Question.objects.filter(book__slug=self.kwargs['slug']).prefetch_related(
            'answers__user'
        )

    def perform_create(self, serializer):
        book = generics.get_object_or_404(Book, slug=self.kwargs['slug'])
        serializer.save(user=self.request.user, book=book)


class AnswerCreateView(generics.CreateAPIView):
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        question = generics.get_object_or_404(Question, pk=self.kwargs['pk'])
        serializer.save(user=self.request.user, question=question)


class FriendsPopularBooksView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        from books.serializers import BookListSerializer

        return BookListSerializer

    def get_queryset(self):
        following_ids = Follow.objects.filter(follower=self.request.user).values_list(
            'following_id', flat=True
        )
        return (
            Book.objects.filter(shelf_items__user_id__in=following_ids)
            .annotate(friend_count=Count('shelf_items', distinct=True))
            .select_related('author')
            .prefetch_related('genres')
            .order_by('-friend_count')[:12]
        )


class FeedView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        following_ids = Follow.objects.filter(follower=self.request.user).values_list(
            'following_id', flat=True
        )
        return Activity.objects.filter(user_id__in=list(following_ids) + [self.request.user.id]).select_related(
            'user', 'book__author', 'review__user'
        )


class UserAchievementsView(APIView):
    def get(self, request, username):
        from .achievements import build_achievements

        user = generics.get_object_or_404(User, username=username)
        lang = 'uz' if request.query_params.get('lang') == 'uz' else 'en'
        return Response(build_achievements(user, lang))


class UserStatsView(APIView):
    def get(self, request, username):
        user = generics.get_object_or_404(User, username=username)
        reviews = Review.objects.filter(user=user)
        genre_counts = (
            ShelfItem.objects.filter(user=user, status=ShelfItem.READ)
            .values('book__genres__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:6]
        )
        from django.utils import timezone

        return Response({
            'books_read': ShelfItem.objects.filter(user=user, status=ShelfItem.READ).count(),
            'read_this_year': DiaryEntry.objects.filter(
                user=user, date_read__year=timezone.localdate().year
            ).count(),
            'reading': ShelfItem.objects.filter(user=user, status=ShelfItem.READING).count(),
            'want': ShelfItem.objects.filter(user=user, status=ShelfItem.WANT).count(),
            'reviews': reviews.count(),
            'avg_rating': round(reviews.aggregate(a=Avg('rating'))['a'] or 0, 1),
            'genres': [
                {'name': g['book__genres__name'] or '—', 'count': g['count']}
                for g in genre_counts
            ],
        })
