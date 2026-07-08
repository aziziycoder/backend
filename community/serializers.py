from rest_framework import serializers

from books.serializers import BookListSerializer
from users.serializers import UserMiniSerializer
from .models import (
    Activity,
    Answer,
    DiaryEntry,
    ListComment,
    Question,
    ReadingList,
    Review,
    ReviewComment,
    ShelfItem,
)


def validate_half_star(value):
    if value is None:
        return value
    doubled = value * 2
    if doubled != int(doubled) or not 1 <= doubled <= 10:
        raise serializers.ValidationError('Rating must be between 0.5 and 5 in 0.5 steps.')
    return value


class ReviewCommentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = ReviewComment
        fields = ('id', 'user', 'text', 'created_at')


class ReviewSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = ReviewCommentSerializer(many=True, read_only=True)
    viewer_has_read = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            'id', 'user', 'book', 'rating', 'text', 'has_spoiler',
            'likes_count', 'is_liked', 'comments', 'viewer_has_read', 'created_at',
        )

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_viewer_has_read(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if obj.user_id == request.user.id:
            return True  # o'z taqrizi o'ziga hech qachon yashirilmaydi
        return ShelfItem.objects.filter(
            user=request.user, book=obj.book, status=ShelfItem.READ
        ).exists()

    def validate_rating(self, value):
        return validate_half_star(value)



class ShelfItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)

    class Meta:
        model = ShelfItem
        fields = ('id', 'book', 'status', 'updated_at')


class DiaryEntrySerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    book = BookListSerializer(read_only=True)

    class Meta:
        model = DiaryEntry
        fields = ('id', 'user', 'book', 'date_started', 'date_read', 'rating', 'note', 'created_at')

    def validate_rating(self, value):
        return validate_half_star(value)


class ListCommentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = ListComment
        fields = ('id', 'user', 'text', 'created_at')


class ReadingListSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    books_count = serializers.SerializerMethodField()
    covers = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = ReadingList
        fields = (
            'id', 'user', 'title', 'description', 'books_count', 'covers',
            'likes_count', 'is_liked', 'comments_count', 'created_at',
        )

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_books_count(self, obj):
        return obj.items.count()

    def get_covers(self, obj):
        return [
            {'title': i.book.title, 'author': i.book.author.name, 'cover_src': i.book.cover_src}
            for i in obj.items.select_related('book__author')[:4]
        ]


class ReadingListDetailSerializer(ReadingListSerializer):
    books = serializers.SerializerMethodField()
    comments = ListCommentSerializer(many=True, read_only=True)

    class Meta(ReadingListSerializer.Meta):
        fields = ReadingListSerializer.Meta.fields + ('books', 'comments')

    def get_books(self, obj):
        books = [i.book for i in obj.items.select_related('book__author').prefetch_related('book__genres')]
        return BookListSerializer(books, many=True, context=self.context).data


class AnswerSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ('id', 'user', 'text', 'created_at')


class QuestionSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'user', 'text', 'answers', 'created_at')


class ActivitySerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    review = ReviewSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ('id', 'user', 'verb', 'book', 'review', 'created_at')
