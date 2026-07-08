import re

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from community.models import Favorite, Review, ShelfItem

MD_LINK_RE = re.compile(r'\[([^\]]+)\]\([^)]*\)')


def linkify_reply(text):
    """AI javobidagi katalog kitob nomlarini [Nom](/books/slug) linkiga aylantiradi.
    Model noto'g'ri yoki umuman link yozmasa ham linklar to'g'ri ishlashini kafolatlaydi."""
    books = list(Book.objects.values_list('title', 'slug'))
    if not books:
        return text
    # 1) modelning barcha linklarini yechib, faqat matnini qoldiramiz (noto'g'ri havolalar bo'lishi mumkin)
    text = MD_LINK_RE.sub(lambda m: m.group(1), text)
    # 2) katalog nomlarini o'zimiz to'g'ri slug bilan linklaymiz (uzunroq nomlar birinchi)
    books.sort(key=lambda b: -len(b[0]))
    slug_by_title = {t: s for t, s in books}
    alt = re.compile('|'.join(re.escape(t) for t, _ in books))
    return alt.sub(lambda m: f'[{m.group(0)}](/books/{slug_by_title[m.group(0)]})', text)

SYSTEM_TEMPLATE = """You are the warm, knowledgeable book-recommendation assistant for "Badiiyat", a social network for book lovers.

STRICT RULES:
- Recommend ONLY books that appear in the CATALOG below. Never invent titles, authors, or slugs that are not in the catalog.
- Every time you mention a catalog book, you MUST write it as a Markdown link in exactly this form: [Exact Title](/books/slug) — using the slug from the catalog. Never mention a catalog book without this link.
- Personalize suggestions using the READER PROFILE (their ratings, favorites and genres) whenever it is available. Explain briefly WHY each book fits them.
- Keep replies concise and friendly, a few short paragraphs at most. {lang_line}
- If the catalog has nothing suitable, say so honestly and offer the closest alternatives.
- Only discuss books and reading. Politely steer other topics back to books.

CATALOG (title | author | genres | slug):
{catalog}

READER PROFILE:
{profile}
"""


def build_catalog():
    lines = []
    for b in Book.objects.select_related('author').prefetch_related('genres').order_by('title'):
        genres = ', '.join(g.name for g in b.genres.all()) or '—'
        year = b.published_year or '—'
        lines.append(f'- {b.title} | {b.author.name} | {genres} | {year} | {b.slug}')
    return '\n'.join(lines) or '(catalog is empty)'


def build_profile(user):
    if not user or not user.is_authenticated:
        return 'Anonymous visitor — no reading history yet. Give popular, well-rounded suggestions.'

    parts = [f'Username: {user.username}']

    reviews = Review.objects.filter(user=user).select_related('book')
    if reviews.exists():
        rated = '; '.join(f'{r.book.title} ({r.rating}/5)' for r in reviews[:15])
        parts.append(f'Rated books: {rated}')

    favs = Favorite.objects.filter(user=user).select_related('book')
    if favs.exists():
        parts.append('Favorite books: ' + ', '.join(f.book.title for f in favs[:10]))

    for status_key, label in (
        (ShelfItem.READ, 'Has read'),
        (ShelfItem.READING, 'Currently reading'),
        (ShelfItem.WANT, 'Wants to read'),
    ):
        items = ShelfItem.objects.filter(user=user, status=status_key).select_related('book')
        if items.exists():
            parts.append(f'{label}: ' + ', '.join(i.book.title for i in items[:15]))

    genre_names = (
        ShelfItem.objects.filter(user=user, status=ShelfItem.READ)
        .values_list('book__genres__name', flat=True)
    )
    genres = sorted({g for g in genre_names if g})
    if genres:
        parts.append('Favorite genres: ' + ', '.join(genres))

    return '\n'.join(parts)


def sanitize_history(raw):
    messages = []
    for m in raw[-12:]:
        role = m.get('role')
        content = (m.get('content') or '').strip()
        if role in ('user', 'assistant') and content:
            messages.append({'role': role, 'content': content[:2000]})
    return messages


class ChatView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not settings.OPENAI_API_KEY:
            return Response(
                {'detail': 'AI is not configured (missing OPENAI_API_KEY).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        history = sanitize_history(request.data.get('messages', []))
        if not history or history[-1]['role'] != 'user':
            return Response({'detail': 'No user message.'}, status=status.HTTP_400_BAD_REQUEST)

        lang = 'uz' if request.data.get('lang') == 'uz' else 'en'
        lang_line = (
            'Always answer in Uzbek (o\'zbekcha).'
            if lang == 'uz'
            else 'Always answer in English.'
        )
        system = SYSTEM_TEMPLATE.format(
            lang_line=lang_line,
            catalog=build_catalog(),
            profile=build_profile(request.user),
        )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            completion = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{'role': 'system', 'content': system}] + history,
                temperature=0.7,
                max_tokens=700,
            )
            reply = completion.choices[0].message.content
        except Exception as exc:  # noqa: BLE001
            return Response(
                {'detail': f'AI request failed: {exc}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'reply': linkify_reply(reply)})
