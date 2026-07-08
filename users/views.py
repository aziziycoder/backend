from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Follow
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    search_fields = ['username']


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'


class UserFollowersView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(
            following_set__following__username=self.kwargs['username']
        ).order_by('username')


class UserFollowingView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(
            follower_set__follower__username=self.kwargs['username']
        ).order_by('username')


class TopUsersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        users = (
            User.objects.filter(is_active=True)
            .annotate(
                reviews_count=Count('reviews', distinct=True),
                likes_received=Count('reviews__likes', distinct=True),
                comments_received=Count('reviews__comments', distinct=True),
                books_read=Count('shelf', filter=Q(shelf__status='read'), distinct=True),
            )
            .filter(reviews_count__gt=0)
            .order_by('-likes_received', '-comments_received', '-reviews_count')[:20]
        )
        return Response([
            {
                'id': u.id,
                'username': u.username,
                'avatar': u.avatar.url if u.avatar else None,
                'bio': u.bio,
                'reviews_count': u.reviews_count,
                'likes_received': u.likes_received,
                'comments_received': u.comments_received,
                'books_read': u.books_read,
                'score': u.likes_received + u.comments_received,
            }
            for u in users
        ])


class FollowToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target = generics.get_object_or_404(User, username=username)
        if target == request.user:
            return Response({'detail': 'Cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if not created:
            follow.delete()
        return Response({'following': created})
