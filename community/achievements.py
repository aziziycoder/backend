"""Yutuqlar (achievements) — foydalanuvchi ma'lumotlaridan real vaqtda hisoblanadi.
Alohida jadval yoki signal kerak emas: mavjud statistikadan progress bilan chiqariladi."""
from collections import Counter

from books.models import Book
from .models import (
    DiaryEntry,
    Favorite,
    ReadingList,
    Review,
    ReviewLike,
    ShelfItem,
)


def _stats(user):
    read_ids = list(
        ShelfItem.objects.filter(user=user, status=ShelfItem.READ).values_list('book_id', flat=True)
    )
    genre_counts = Counter(
        name
        for name in Book.objects.filter(id__in=read_ids).values_list('genres__name', flat=True)
        if name
    )
    from django.utils import timezone

    return {
        'books_read': len(read_ids),
        'reviews': Review.objects.filter(user=user).count(),
        'five_stars': Review.objects.filter(user=user, rating=5).count(),
        'likes_received': ReviewLike.objects.filter(review__user=user).count(),
        'followers': user.follower_set.count(),
        'following': user.following_set.count(),
        'diary': DiaryEntry.objects.filter(user=user).count(),
        'this_year': DiaryEntry.objects.filter(
            user=user, date_read__year=timezone.localdate().year
        ).count(),
        'lists': ReadingList.objects.filter(user=user).count(),
        'threads': user.threads.count(),
        'favorites': Favorite.objects.filter(user=user).count(),
        'genres': genre_counts,
    }


# (key, icon, target, stat, {uz, en title}, {uz, en desc})
# stat "genre:Fantasy" -> o'sha janrdagi o'qilgan kitoblar soni
DEFS = [
    ('first-book', 'BookOpen', 1, 'books_read', ('Ilk qadam', 'First step'),
     ('Birinchi kitobni o‘qidingiz', 'Read your first book')),
    ('reader-10', 'Library', 10, 'books_read', ('Kitobxon', 'Reader'),
     ('10 ta kitob o‘qidingiz', 'Read 10 books')),
    ('reader-25', 'Library', 25, 'books_read', ('Kitobsevar', 'Bibliophile'),
     ('25 ta kitob o‘qidingiz', 'Read 25 books')),
    ('reader-50', 'Trophy', 50, 'books_read', ('Tirik kutubxona', 'Living library'),
     ('50 ta kitob o‘qidingiz', 'Read 50 books')),
    ('reader-100', 'Crown', 100, 'books_read', ('Afsona', 'Legend'),
     ('100 ta kitob o‘qidingiz', 'Read 100 books')),

    ('fantasy-10', 'Wand2', 10, 'genre:Fantasy', ('Sehrgar', 'Wizard'),
     ('10 ta fantastika o‘qidingiz', 'Read 10 fantasy books')),
    ('classic-10', 'Landmark', 10, 'genre:Classic', ('Klassik did', 'Classicist'),
     ('10 ta klassika o‘qidingiz', 'Read 10 classics')),
    ('philosophy-5', 'Brain', 5, 'genre:Philosophy', ('Faylasuf', 'Philosopher'),
     ('5 ta falsafiy asar o‘qidingiz', 'Read 5 philosophy books')),

    ('critic-1', 'PenLine', 1, 'reviews', ('Munaqqid', 'Critic'),
     ('Birinchi taqrizni yozdingiz', 'Wrote your first review')),
    ('critic-10', 'PenLine', 10, 'reviews', ('Taniqli munaqqid', 'Renowned critic'),
     ('10 ta taqriz yozdingiz', 'Wrote 10 reviews')),
    ('perfectionist', 'Star', 10, 'five_stars', ('Mukammallik', 'Perfectionist'),
     ('10 ta kitobga 5 yulduz berdingiz', 'Gave 5 stars to 10 books')),

    ('popular-10', 'Users', 10, 'followers', ('Mashhur', 'Popular'),
     ('10 ta obunachi', '10 followers')),
    ('social', 'UserPlus', 5, 'following', ('Do‘stona', 'Sociable'),
     ('5 kishiga obuna bo‘ldingiz', 'Followed 5 people')),
    ('beloved', 'Heart', 25, 'likes_received', ('Sevimli muallif', 'Beloved author'),
     ('Taqrizlaringiz 25 marta yoqtirildi', 'Got 25 likes on your reviews')),

    ('diarist', 'NotebookPen', 10, 'diary', ('Kunchi', 'Diarist'),
     ('Kundalikka 10 marta yozdingiz', 'Logged 10 diary entries')),
    ('year-goal', 'Flame', 12, 'this_year', ('Yillik maqsad', 'Yearly goal'),
     ('Bu yil 12 ta kitob o‘qidingiz', 'Read 12 books this year')),
    ('collector', 'ListChecks', 3, 'lists', ('Kollektsioner', 'Collector'),
     ('3 ta ro‘yxat yaratdingiz', 'Created 3 lists')),
    ('conversationalist', 'MessagesSquare', 3, 'threads', ('Suhbatdosh', 'Conversationalist'),
     ('Forumda 3 ta mavzu ochdingiz', 'Started 3 forum threads')),
]


def build_achievements(user, lang='uz'):
    s = _stats(user)
    i = 0 if lang == 'uz' else 1
    out = []
    for key, icon, target, stat, title, desc in DEFS:
        if stat.startswith('genre:'):
            value = s['genres'].get(stat.split(':', 1)[1], 0)
        else:
            value = s[stat]
        out.append({
            'key': key,
            'icon': icon,
            'title': title[i],
            'desc': desc[i],
            'target': target,
            'progress': min(value, target),
            'earned': value >= target,
        })
    # olinganlar birinchi, keyin progressga qarab
    out.sort(key=lambda a: (not a['earned'], -(a['progress'] / a['target'])))
    return out
