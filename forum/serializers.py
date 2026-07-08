from rest_framework import serializers

from books.serializers import BookListSerializer
from users.serializers import UserMiniSerializer
from .models import ForumPost, ForumThread


def participants_count(thread):
    ids = {p.author_id for p in thread.posts.all()}
    ids.add(thread.author_id)
    return len(ids)


class ForumPostSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = ForumPost
        fields = ('id', 'author', 'text', 'created_at')


class ThreadListSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    posts_count = serializers.IntegerField(source='posts.count', read_only=True)
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumThread
        fields = (
            'id', 'title', 'slug', 'body', 'author', 'book',
            'posts_count', 'participants_count', 'last_activity', 'created_at',
        )

    def get_participants_count(self, obj):
        return participants_count(obj)


class ThreadDetailSerializer(ThreadListSerializer):
    posts = ForumPostSerializer(many=True, read_only=True)

    class Meta(ThreadListSerializer.Meta):
        fields = ThreadListSerializer.Meta.fields + ('posts',)
