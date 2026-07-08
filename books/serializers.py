from django.db.models import Avg
from rest_framework import serializers

from community.models import Favorite, ShelfItem
from .models import Author, Book, Character, Genre


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name', 'bio', 'photo')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ('id', 'name', 'role', 'description')


class BookListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    cover_src = serializers.ReadOnlyField()

    class Meta:
        model = Book
        fields = (
            'id', 'title', 'slug', 'author', 'genres', 'cover_src',
            'published_year', 'pages', 'avg_rating', 'ratings_count',
        )

    def get_avg_rating(self, obj):
        avg = obj.reviews.aggregate(a=Avg('rating'))['a']
        return round(avg, 1) if avg else None

    def get_ratings_count(self, obj):
        return obj.reviews.count()


class BookDetailSerializer(BookListSerializer):
    characters = CharacterSerializer(many=True, read_only=True)
    my_shelf_status = serializers.SerializerMethodField()
    my_shelf_started = serializers.SerializerMethodField()
    shelf_counts = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta(BookListSerializer.Meta):
        fields = BookListSerializer.Meta.fields + (
            'description', 'characters', 'my_shelf_status', 'my_shelf_started',
            'shelf_counts', 'favorites_count', 'is_favorite',
        )

    def get_favorites_count(self, obj):
        return obj.favorites.count()

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, book=obj).exists()

    def get_shelf_counts(self, obj):
        from django.db.models import Count

        counts = {'want': 0, 'reading': 0, 'read': 0}
        for row in obj.shelf_items.values('status').annotate(c=Count('id')):
            counts[row['status']] = row['c']
        return counts

    def get_my_shelf_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        item = ShelfItem.objects.filter(user=request.user, book=obj).first()
        return item.status if item else None

    def get_my_shelf_started(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        item = ShelfItem.objects.filter(user=request.user, book=obj).first()
        return item.started_on if item else None


class AuthorDetailSerializer(AuthorSerializer):
    books = BookListSerializer(many=True, read_only=True)

    class Meta(AuthorSerializer.Meta):
        fields = AuthorSerializer.Meta.fields + ('books',)
