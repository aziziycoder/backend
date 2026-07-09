from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from books.views import (
    AuthorDetailView,
    BookDetailView,
    BookListView,
    GenreListView,
    SearchView,
)
from community.views import (
    AnswerCreateView,
    BookChallengeView,
    ChallengeMarkView,
    BookDiaryCreateView,
    BookFavoriteToggleView,
    ListCommentCreateView,
    ListLikeToggleView,
    MyFeaturedView,
    UserFavoritesView,
    UserFeaturedView,
    BookQuestionListCreateView,
    BookReviewListCreateView,
    DiaryEntryDeleteView,
    FeedView,
    FriendsDiaryView,
    FriendsPopularBooksView,
    ReadingListBookView,
    ReadingListDetailView,
    ReadingListListCreateView,
    RecentReviewsView,
    ReviewCommentCreateView,
    ReviewLikeToggleView,
    ShelfView,
    UserAchievementsView,
    UserDiaryView,
    UserListsView,
    UserReviewsView,
    UserShelfView,
    UserStatsView,
)
from assistant.views import (
    BookQuizView,
    ChatView,
    CharacterChatView,
    ReadingTasteView,
    ReviewCheckView,
    ReviewSummaryView,
    ThreadIdeasView,
)
from forum.views import ThreadDetailView, ThreadListCreateView, ThreadPostCreateView
from users.views import (
    FollowToggleView,
    MeView,
    RegisterView,
    TopUsersView,
    UserDetailView,
    UserFollowersView,
    UserFollowingView,
    UserListView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # auth
    path('api/auth/register/', RegisterView.as_view()),
    path('api/auth/token/', TokenObtainPairView.as_view()),
    path('api/auth/token/refresh/', TokenRefreshView.as_view()),

    # users
    path('api/users/me/', MeView.as_view()),
    path('api/users/me/featured/', MyFeaturedView.as_view()),
    path('api/users/top/', TopUsersView.as_view()),
    path('api/users/', UserListView.as_view()),
    path('api/users/<str:username>/', UserDetailView.as_view()),
    path('api/users/<str:username>/followers/', UserFollowersView.as_view()),
    path('api/users/<str:username>/following/', UserFollowingView.as_view()),
    path('api/users/<str:username>/follow/', FollowToggleView.as_view()),
    path('api/users/<str:username>/shelf/', UserShelfView.as_view()),
    path('api/users/<str:username>/reviews/', UserReviewsView.as_view()),
    path('api/users/<str:username>/stats/', UserStatsView.as_view()),
    path('api/users/<str:username>/achievements/', UserAchievementsView.as_view()),
    path('api/users/<str:username>/diary/', UserDiaryView.as_view()),
    path('api/users/<str:username>/lists/', UserListsView.as_view()),
    path('api/users/<str:username>/favorites/', UserFavoritesView.as_view()),
    path('api/users/<str:username>/featured/', UserFeaturedView.as_view()),

    # books
    path('api/search/', SearchView.as_view()),
    path('api/authors/<int:pk>/', AuthorDetailView.as_view()),
    path('api/genres/', GenreListView.as_view()),
    path('api/books/', BookListView.as_view()),
    # e'tibor: <slug> patternidan OLDIN turishi shart
    path('api/books/friends-popular/', FriendsPopularBooksView.as_view()),
    path('api/books/<slug:slug>/', BookDetailView.as_view()),
    path('api/books/<slug:slug>/reviews/', BookReviewListCreateView.as_view()),
    path('api/books/<slug:slug>/shelf/', ShelfView.as_view()),
    path('api/books/<slug:slug>/questions/', BookQuestionListCreateView.as_view()),
    path('api/books/<slug:slug>/diary/', BookDiaryCreateView.as_view()),
    path('api/books/<slug:slug>/favorite/', BookFavoriteToggleView.as_view()),
    path('api/books/<slug:slug>/challenge/', BookChallengeView.as_view()),
    path('api/books/<slug:slug>/challenge/mark/', ChallengeMarkView.as_view()),
    path('api/questions/<int:pk>/answers/', AnswerCreateView.as_view()),

    # diary & lists
    path('api/diary/friends/', FriendsDiaryView.as_view()),
    path('api/diary/<int:pk>/', DiaryEntryDeleteView.as_view()),
    path('api/lists/', ReadingListListCreateView.as_view()),
    path('api/lists/<int:pk>/', ReadingListDetailView.as_view()),
    path('api/lists/<int:pk>/like/', ListLikeToggleView.as_view()),
    path('api/lists/<int:pk>/comments/', ListCommentCreateView.as_view()),
    path('api/lists/<int:pk>/books/', ReadingListBookView.as_view()),
    path('api/lists/<int:pk>/books/<slug:slug>/', ReadingListBookView.as_view()),

    # community
    path('api/reviews/<int:pk>/like/', ReviewLikeToggleView.as_view()),
    path('api/reviews/<int:pk>/comments/', ReviewCommentCreateView.as_view()),
    path('api/feed/', FeedView.as_view()),
    path('api/reviews/recent/', RecentReviewsView.as_view()),

    # AI assistant
    path('api/chat/', ChatView.as_view()),
    path('api/characters/<int:pk>/chat/', CharacterChatView.as_view()),
    path('api/books/<slug:slug>/quiz/', BookQuizView.as_view()),
    path('api/books/<slug:slug>/review-summary/', ReviewSummaryView.as_view()),
    path('api/books/<slug:slug>/thread-ideas/', ThreadIdeasView.as_view()),
    path('api/users/<str:username>/taste/', ReadingTasteView.as_view()),
    path('api/reviews/check/', ReviewCheckView.as_view()),

    # forum
    path('api/forums/', ThreadListCreateView.as_view()),
    path('api/forums/<slug:slug>/', ThreadDetailView.as_view()),
    path('api/forums/<slug:slug>/posts/', ThreadPostCreateView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
