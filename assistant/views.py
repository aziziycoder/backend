import json
import re

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book, Character
from community.models import Favorite, Review, ShelfItem


def run_openai(messages, max_tokens=700, temperature=0.7, json_mode=False):
    """OpenAI chat chaqiruvi — barcha AI funksiyalari shuni ishlatadi."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    kwargs = {
        'model': settings.OPENAI_MODEL,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    if json_mode:
        kwargs['response_format'] = {'type': 'json_object'}
    return client.chat.completions.create(**kwargs).choices[0].message.content


def lang_word(lang):
    return "Uzbek (o'zbekcha)" if lang == 'uz' else 'English'


def get_lang(request):
    return 'uz' if request.query_params.get('lang') == 'uz' else 'en'


def book_context(book):
    chars = '; '.join(
        f'{c.name} ({c.role}): {c.description}' for c in book.characters.all()
    ) or 'none listed'
    genres = ', '.join(g.name for g in book.genres.all()) or '—'
    return (
        f'Title: {book.title}\nAuthor: {book.author.name}\n'
        f'Year: {book.published_year or "—"}\nGenres: {genres}\n'
        f'Description: {book.description or "—"}\nCharacters: {chars}'
    )


def ai_unconfigured():
    return Response(
        {'detail': 'AI is not configured (missing OPENAI_API_KEY).'},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def ai_failed(exc):
    return Response({'detail': f'AI request failed: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

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
            reply = run_openai([{'role': 'system', 'content': system}] + history)
        except Exception as exc:  # noqa: BLE001
            return ai_failed(exc)

        return Response({'reply': linkify_reply(reply)})


class CharacterChatView(APIView):
    """#1 Qahramon bilan suhbat — AI kitob qahramoni roliga kiradi."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        if not settings.OPENAI_API_KEY:
            return ai_unconfigured()
        character = generics.get_object_or_404(
            Character.objects.select_related('book__author'), pk=pk
        )
        history = sanitize_history(request.data.get('messages', []))
        if not history or history[-1]['role'] != 'user':
            return Response({'detail': 'No user message.'}, status=status.HTTP_400_BAD_REQUEST)

        lang = 'uz' if request.data.get('lang') == 'uz' else 'en'
        system = (
            f'You ARE {character.name}, a character from the book "{character.book.title}" '
            f'by {character.book.author.name}. Your role: {character.role or "character"}. '
            f'About you: {character.description or "—"}\n\n'
            f'Stay fully in character — speak as {character.name} in first person, with their '
            f'personality and worldview. Never say you are an AI. Keep replies short (2-4 sentences). '
            f'Answer in {lang_word(lang)}. If asked about things beyond the book, answer as the '
            f'character would imagine, staying in the spirit of the story.'
        )
        try:
            reply = run_openai(
                [{'role': 'system', 'content': system}] + history, max_tokens=300, temperature=0.9
            )
        except Exception as exc:  # noqa: BLE001
            return ai_failed(exc)
        return Response({'reply': reply})


class BookQuizView(APIView):
    """#3 AI viktorina — kitob bo'yicha 5 ta ko'p tanlovli savol."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        if not settings.OPENAI_API_KEY:
            return ai_unconfigured()
        book = generics.get_object_or_404(
            Book.objects.select_related('author').prefetch_related('genres', 'characters'), slug=slug
        )
        lang = get_lang(request)
        system = (
            'You create book quizzes. Given a book, produce exactly 5 multiple-choice questions '
            f'that test whether someone truly read and understood it. Write everything in {lang_word(lang)}. '
            'Each question has exactly 4 options and one correct answer. Base questions on plot, '
            'characters, themes and setting. Return ONLY JSON: '
            '{"questions":[{"q":"...","options":["a","b","c","d"],"answer":0}]} '
            'where "answer" is the 0-based index of the correct option.'
        )
        user_msg = f'Book:\n{book_context(book)}'
        try:
            raw = run_openai(
                [{'role': 'system', 'content': system}, {'role': 'user', 'content': user_msg}],
                max_tokens=900,
                temperature=0.6,
                json_mode=True,
            )
            data = json.loads(raw)
            questions = data.get('questions', [])
            # xavfsizlik: faqat to'g'ri tuzilgan savollarni qoldiramiz
            clean = [
                q for q in questions
                if isinstance(q.get('options'), list)
                and len(q['options']) == 4
                and isinstance(q.get('answer'), int)
                and 0 <= q['answer'] <= 3
                and q.get('q')
            ]
        except Exception as exc:  # noqa: BLE001
            return ai_failed(exc)
        if not clean:
            return ai_failed('empty quiz')
        return Response({'questions': clean[:5]})


class ReviewSummaryView(APIView):
    """#5 Jamoa fikri xulosasi — barcha taqrizlarni bitta paragrafga jamlaydi."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        if not settings.OPENAI_API_KEY:
            return ai_unconfigured()
        book = generics.get_object_or_404(Book, slug=slug)
        reviews = list(book.reviews.exclude(text='').values_list('rating', 'text')[:40])
        if len(reviews) < 2:
            return Response({'summary': None})
        lang = get_lang(request)
        joined = '\n'.join(f'- ({r}/5) {t}' for r, t in reviews)
        system = (
            'You summarize reader reviews of a book into one short, balanced paragraph '
            '(3-4 sentences): the general consensus, what readers praise, and any common '
            f'criticism. Be neutral and specific. Write in {lang_word(lang)}. No spoilers.'
        )
        try:
            summary = run_openai(
                [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': f'Book: {book.title}\nReviews:\n{joined}'},
                ],
                max_tokens=300,
                temperature=0.5,
            )
        except Exception as exc:  # noqa: BLE001
            return ai_failed(exc)
        return Response({'summary': summary, 'count': len(reviews)})


class ThreadIdeasView(APIView):
    """#6 Forum mavzu generatori — kitob uchun 3 ta muhokama savoli."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        if not settings.OPENAI_API_KEY:
            return ai_unconfigured()
        book = generics.get_object_or_404(
            Book.objects.select_related('author').prefetch_related('characters'), slug=slug
        )
        lang = get_lang(request)
        system = (
            'You suggest engaging book-club discussion questions. Given a book, return 3 short, '
            f'thought-provoking discussion prompts in {lang_word(lang)}. Return ONLY JSON: '
            '{"ideas":["...","...","..."]}'
        )
        try:
            raw = run_openai(
                [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': f'Book:\n{book_context(book)}'},
                ],
                max_tokens=400,
                json_mode=True,
            )
            ideas = [i for i in json.loads(raw).get('ideas', []) if isinstance(i, str) and i.strip()]
        except Exception as exc:  # noqa: BLE001
            return ai_failed(exc)
        return Response({'ideas': ideas[:3]})


class ReviewCheckView(APIView):
    """Taqriz joylashdan oldin: AI bilan yozilganmi va spoiler bormi tekshiradi."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not settings.OPENAI_API_KEY:
            # AI yo'q bo'lsa — bloklamaymiz, toza deb hisoblaymiz
            return Response({'ai_generated': False, 'spoiler': False, 'note': ''})
        text = (request.data.get('text') or '').strip()
        if len(text) < 20:
            return Response({'ai_generated': False, 'spoiler': False, 'note': ''})
        lang = 'uz' if request.data.get('lang') == 'uz' else 'en'
        system = (
            'You check whether a book review reveals spoilers. Return ONLY JSON: '
            '{"spoiler": bool, "note": "..."}. '
            'spoiler = true if it reveals major plot twists, key deaths, or the ending. '
            f'note = one short sentence in {lang_word(lang)} explaining, or "" if clean.'
        )
        try:
            raw = run_openai(
                [{'role': 'system', 'content': system}, {'role': 'user', 'content': text[:2000]}],
                max_tokens=120,
                temperature=0,
                json_mode=True,
            )
            data = json.loads(raw)
        except Exception:  # noqa: BLE001
            # tekshiruv ishlamasa — joylashga to'sqinlik qilmaymiz
            return Response({'spoiler': False, 'note': ''})
        return Response({'spoiler': bool(data.get('spoiler')), 'note': str(data.get('note') or '')})


class ReadingTasteView(APIView):
    """#2 Kitobxonlik DNK'si — o'qish tarixidan shaxsiyat tavsifi."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        if not settings.OPENAI_API_KEY:
            return ai_unconfigured()
        from django.contrib.auth import get_user_model

        user = generics.get_object_or_404(get_user_model(), username=username)
        read = list(
            ShelfItem.objects.filter(user=user, status=ShelfItem.READ)
            .select_related('book')[:30]
        )
        if len(read) < 2:
            return Response({'text': None})
        lang = get_lang(request)
        rated = {r.book_id: r.rating for r in Review.objects.filter(user=user)}
        genres = sorted({
            g for g in ShelfItem.objects.filter(user=user, status=ShelfItem.READ)
            .values_list('book__genres__name', flat=True) if g
        })
        books = '; '.join(
            f'{i.book.title}' + (f' ({rated[i.book_id]}/5)' if i.book_id in rated else '')
            for i in read
        )
        system = (
            'You are a witty literary analyst. From a reader\'s history, write a fun, flattering '
            '2-3 sentence "reading personality" describing what kind of reader they are and what '
            f'draws them to books. Address them as "you". Warm and playful. Write in {lang_word(lang)}.'
        )
        try:
            text = run_openai(
                [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': f'Read books: {books}\nFavorite genres: {", ".join(genres) or "—"}'},
                ],
                max_tokens=250,
                temperature=0.85,
            )
        except Exception as exc:  # noqa: BLE001
            return ai_failed(exc)
        return Response({'text': text})
