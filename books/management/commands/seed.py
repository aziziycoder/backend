from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from datetime import date

from books.models import Author, Book, Character, Genre
from community.models import (
    Activity,
    Answer,
    DiaryEntry,
    Favorite,
    ListComment,
    ListLike,
    Question,
    ReadingList,
    ReadingListItem,
    Review,
    ReviewComment,
    ReviewLike,
    ShelfItem,
)
from forum.models import ForumPost, ForumThread
from users.models import Follow

User = get_user_model()

AUTHOR_BIOS = {
    'Abdulla Qodiriy': "O'zbek adabiyotining asoschilaridan biri (1894–1938), birinchi o'zbek romani \"O'tkan kunlar\" muallifi. Jadidchilik harakatining faol vakili bo'lgan, 1938-yilda qatag'on qurboni bo'lgan.",
    'George Orwell': 'English novelist and essayist (1903–1950), famous for "1984" and "Animal Farm". His works explore totalitarianism, surveillance and the misuse of language in politics.',
    'F. Scott Fitzgerald': 'American novelist (1896–1940), the voice of the Jazz Age. "The Great Gatsby" is considered one of the greatest American novels.',
    'Fyodor Dostoevsky': 'Russian novelist and philosopher (1821–1881). His psychological masterpieces — "Crime and Punishment", "The Brothers Karamazov", "The Idiot" — explore the depths of the human soul.',
    'J.K. Rowling': 'British author (b. 1965), creator of the Harry Potter series — the best-selling book series in history, translated into more than 80 languages.',
    'Paulo Coelho': 'Brazilian novelist (b. 1947). "The Alchemist" has sold over 65 million copies and become one of the most translated books by a living author.',
    'Antoine de Saint-Exupéry': 'French writer and pioneering aviator (1900–1944). "The Little Prince" is one of the most-translated books in the world.',
    'Yuval Noah Harari': 'Israeli historian and professor (b. 1976), author of the international bestsellers "Sapiens", "Homo Deus" and "21 Lessons for the 21st Century".',
    "Abdulhamid Cho'lpon": "O'zbek shoiri, yozuvchi va dramaturg (1897–1938). Yangi o'zbek she'riyatining asoschisi, \"Kecha va kunduz\" romani muallifi. Qatag'on qurboni.",
    "O'tkir Hoshimov": "O'zbek adabiyotining yirik vakillaridan biri (1941–2013). O'zbekiston xalq yozuvchisi. Inson ruhiyatini tasvirlovchi xalqona asarlari bilan tanilgan.",
    "Pirimqul Qodirov": "O'zbekiston xalq yozuvchisi (1928–2010), mashhur tarixiy romanlar muallifi. \"Yulduzli tunlar\" asari orqali Boburning murakkab hayot yo'lini yuksak mahorat bilan yoritgan.",
    "G'afur G'ulom": "O'zbekiston xalq shoiri va yozuvchisi (1903–1966), o'zbek adabiyotida yumoristik qissa janrining yirik vakili.",
}

LIKES = [
    ('javohir', 'aziza', "O'tkan kunlar"),
    ('bekzod', 'aziza', "O'tkan kunlar"),
    ('aziza', 'javohir', '1984'),
    ('bekzod', 'javohir', '1984'),
    ('aziza', 'bekzod', 'Crime and Punishment'),
    ('javohir', 'bekzod', "O'tkan kunlar"),
    ('bekzod', 'aziza', 'The Little Prince'),
]

GENRES = ['Classic', 'Fantasy', 'Dystopia', 'Romance', 'Historical', 'Philosophy', 'Adventure', 'Drama']

BOOKS = [
    {
        'title': "O'tkan kunlar",
        'author': 'Abdulla Qodiriy',
        'year': 1926, 'pages': 400,
        'genres': ['Classic', 'Historical', 'Romance'],
        'description': "O'zbek adabiyotining ilk romani. Otabek va Kumushbibi muhabbati orqali XIX asr Turkiston hayoti tasvirlanadi.",
        'cover': 'https://covers.openlibrary.org/b/isbn/9781838005344-L.jpg?default=false',
        'characters': [
            ('Otabek', 'Bosh qahramon', "Toshkentlik savdogar yigit, ma'rifatparvar."),
            ('Kumushbibi', 'Bosh qahramon', "Marg'ilonlik go'zal qiz, Otabekning sevgilisi."),
            ('Yusufbek hoji', 'Yordamchi qahramon', 'Otabekning otasi, obro\'li inson.'),
        ],
    },
    {
        'title': 'Mehrobdan chayon',
        'author': 'Abdulla Qodiriy',
        'year': 1929, 'pages': 320,
        'genres': ['Classic', 'Historical'],
        'description': "Qo'qon xonligi davridagi saroy fitnalari va Anvar mirzo taqdiri haqidagi roman.",
        'cover': '',
        'characters': [
            ('Anvar', 'Bosh qahramon', "Xon saroyida mirzo bo'lib ishlaydigan iste'dodli yigit."),
            ('Ra\'no', 'Bosh qahramon', 'Anvarning sevgilisi.'),
        ],
    },
    {
        'title': '1984',
        'author': 'George Orwell',
        'year': 1949, 'pages': 328,
        'genres': ['Dystopia', 'Classic'],
        'description': 'A dystopian novel about totalitarian surveillance and the destruction of truth.',
        'cover': 'https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg?default=false',
        'characters': [
            ('Winston Smith', 'Protagonist', 'A low-ranking Party member who secretly hates the regime.'),
            ('Julia', 'Protagonist', "Winston's lover and fellow rebel."),
            ('O\'Brien', 'Antagonist', 'An Inner Party member who betrays Winston.'),
            ('Big Brother', 'Antagonist', 'The ever-watching face of the Party.'),
        ],
    },
    {
        'title': 'The Great Gatsby',
        'author': 'F. Scott Fitzgerald',
        'year': 1925, 'pages': 180,
        'genres': ['Classic', 'Romance'],
        'description': 'The tragic story of Jay Gatsby and his obsessive love for Daisy Buchanan in the Jazz Age.',
        'cover': 'https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg?default=false',
        'characters': [
            ('Jay Gatsby', 'Protagonist', 'A mysterious millionaire chasing a lost love.'),
            ('Nick Carraway', 'Narrator', "Gatsby's neighbor and the story's narrator."),
            ('Daisy Buchanan', 'Protagonist', "The object of Gatsby's obsession."),
        ],
    },
    {
        'title': 'Crime and Punishment',
        'author': 'Fyodor Dostoevsky',
        'year': 1866, 'pages': 671,
        'genres': ['Classic', 'Philosophy', 'Drama'],
        'description': 'A psychological drama about guilt, redemption and the mind of a murderer.',
        'cover': 'https://covers.openlibrary.org/b/isbn/9780143058144-L.jpg?default=false',
        'characters': [
            ('Rodion Raskolnikov', 'Protagonist', 'A poor ex-student who commits a murder to test his theory.'),
            ('Sonya Marmeladova', 'Protagonist', 'A gentle soul who leads Raskolnikov to redemption.'),
            ('Porfiry Petrovich', 'Antagonist', 'The clever investigator.'),
        ],
    },
    {
        'title': "Harry Potter and the Philosopher's Stone",
        'author': 'J.K. Rowling',
        'year': 1997, 'pages': 223,
        'genres': ['Fantasy', 'Adventure'],
        'description': 'An orphan boy discovers he is a wizard and enters the magical world of Hogwarts.',
        'cover': 'https://covers.openlibrary.org/b/isbn/9780590353427-L.jpg?default=false',
        'characters': [
            ('Harry Potter', 'Protagonist', 'The boy who lived.'),
            ('Hermione Granger', 'Protagonist', 'The brightest witch of her age.'),
            ('Ron Weasley', 'Protagonist', "Harry's loyal best friend."),
            ('Voldemort', 'Antagonist', 'The dark lord who murdered Harry\'s parents.'),
        ],
    },
    {
        'title': 'The Alchemist',
        'author': 'Paulo Coelho',
        'year': 1988, 'pages': 208,
        'genres': ['Philosophy', 'Adventure'],
        'description': 'A shepherd boy travels to Egypt in search of treasure and finds his Personal Legend.',
        'cover': 'https://covers.openlibrary.org/b/isbn/9780061122415-L.jpg?default=false',
        'characters': [
            ('Santiago', 'Protagonist', 'A young Andalusian shepherd following his dream.'),
            ('The Alchemist', 'Mentor', 'A wise man who guides Santiago.'),
        ],
    },
    {
        'title': 'The Little Prince',
        'author': 'Antoine de Saint-Exupéry',
        'year': 1943, 'pages': 96,
        'genres': ['Classic', 'Philosophy'],
        'description': 'A poetic tale about a little prince who visits Earth and teaches what truly matters.',
        'cover': 'https://covers.openlibrary.org/b/isbn/9780156012195-L.jpg?default=false',
        'characters': [
            ('The Little Prince', 'Protagonist', 'A boy from asteroid B-612.'),
            ('The Fox', 'Mentor', '"You become responsible, forever, for what you have tamed."'),
        ],
    },
    {
        'title': 'Sapiens: A Brief History of Humankind',
        'author': 'Yuval Noah Harari',
        'year': 2011, 'pages': 443,
        'genres': ['Historical', 'Philosophy'],
        'description': 'How Homo sapiens conquered the world — from the Cognitive Revolution to the present.',
        'cover': 'https://covers.openlibrary.org/b/isbn/9780062316097-L.jpg?default=false',
        'characters': [],
    },
    {
        'title': 'Kecha va kunduz',
        'author': "Abdulhamid Cho'lpon",
        'year': 1936, 'pages': 288,
        'genres': ['Classic', 'Drama'],
        'description': "Cho'lponning jadidchilik davri hayotini aks ettirgan mashhur romani. Zebi taqdiri orqali ayol erki masalasi ko'tariladi.",
        'cover': '',
        'characters': [
            ('Zebi', 'Bosh qahramon', "Taqdir zarbalariga uchragan qishloq qizi."),
            ('Miryoqub', 'Yordamchi qahramon', "Epchil va tadbirkor odam."),
        ],
    },
    {
        'title': "Dunyoning ishlari",
        'author': "O'tkir Hoshimov",
        'year': 1982, 'pages': 250,
        'genres': ['Classic', 'Drama'],
        'description': "O'tkir Hoshimovning eng mashhur qissasi. Har bir bob alohida hikoyalardan iborat bo'lib, ona va bola o'rtasidagi samimiy munosabatlar, mehr-oqibat va urushdan keyingi hayot tasvirlanadi.",
        'cover': '',
        'characters': [
            ('Lutfi', 'Bosh qahramon', "Yozuvchining onasi timsoli, yuksak ma'naviyatli, mehribon ona."),
        ],
    },
    {
        'title': "Ikki eshik orasi",
        'author': "O'tkir Hoshimov",
        'year': 1986, 'pages': 450,
        'genres': ['Classic', 'Historical', 'Drama'],
        'description': "Urush davridagi hayotning qiyinchiliklari, insonlar taqdiri, sadoqat va xiyonat haqida so'zlovchi yirik asar.",
        'cover': '',
        'characters': [
            ('Rano', 'Bosh qahramon', "Sodiq va bardoshli o'zbek ayoli."),
            ('Muzaffar', 'Bosh qahramon', "Qiyinchiliklar bilan katta bo'lgan yosh yigit."),
            ('Umar zakchi', 'Antagonist', "Salbiy obraz, shafqatsiz shaxs."),
        ],
    },
    {
        'title': "Yulduzli tunlar",
        'author': "Pirimqul Qodirov",
        'year': 1979, 'pages': 520,
        'genres': ['Classic', 'Historical', 'Drama'],
        'description': "Zahiriddin Muhammad Boburning murakkab hayoti, shaxsiyati va ijodiy yo'li tasvirlangan mashhur tarixiy roman.",
        'cover': '',
        'characters': [
            ('Bobur', 'Bosh qahramon', "Shoh, sarkarda va buyuk shoir."),
            ('Xonzodabegim', 'Yordamchi qahramon', "Boburning opasi, sadoqatli malika."),
            ('Shayboniyxon', 'Antagonist', "Boburning asosiy raqibi."),
        ],
    },
    {
        'title': "Shum bola",
        'author': "G'afur G'ulom",
        'year': 1936, 'pages': 180,
        'genres': ['Classic', 'Adventure', 'Drama'],
        'description': "G'afur G'ulomning yumoristik qissasi. Yetim qolgan sho'x bolaning hayot qiyinchiliklariga chap berib yurishi hikoya qilinadi.",
        'cover': '',
        'characters': [
            ('Qoravoy', 'Bosh qahramon', "Sho'x, ayyor, aql-idrokli bola."),
            ('Sari boy', 'Yordamchi qahramon', "Baxil va ochko'z boy."),
        ],
    },
    {
        'title': "Animal Farm",
        'author': "George Orwell",
        'year': 1945, 'pages': 112,
        'genres': ['Dystopia', 'Classic', 'Philosophy'],
        'description': "A satirical allegorical novella reflecting events leading up to the Russian Revolution.",
        'cover': 'https://covers.openlibrary.org/b/isbn/9780451526342-L.jpg?default=false',
        'characters': [
            ('Napoleon', 'Antagonist', "The pig who emerges as the leader of the Animal Farm."),
            ('Snowball', 'Protagonist', "Napoleon's rival pig who is expelled from the farm."),
            ('Boxer', 'Protagonist', "The loyal, hard-working cart-horse."),
        ],
    },
]

DEMO_USERS = [
    ('aziza', 'aziza@badiiyat.uz', "Kitob — eng yaxshi do'st 📚"),
    ('javohir', 'javohir@badiiyat.uz', 'Fantastika va antiutopiya muxlisi'),
    ('bekzod', 'bekzod@badiiyat.uz', 'Klassik adabiyot ixlosmandi'),
]

REVIEWS = [
    ('aziza', "O'tkan kunlar", 5, "O'zbek adabiyotining eng buyuk asari! Kumush va Otabek muhabbati hech qachon esdan chiqmaydi."),
    ('javohir', '1984', 5, "Bugungi kunda ham dolzarb. Har bir inson o'qishi shart bo'lgan asar."),
    ('bekzod', 'Crime and Punishment', 5, "Dostoyevskiy inson ruhiyatini hech kim yeta olmagan chuqurlikda ochib beradi."),
    ('aziza', 'The Little Prince', 5, "Kichkina shahzoda — kattalar uchun ertak. Har safar o'qiganimda yangi ma'no topaman."),
    ('javohir', "Harry Potter and the Philosopher's Stone", 4.5, "Bolaligimni eslatadi. Sehrli dunyoga birinchi qadam!"),
    ('bekzod', "O'tkan kunlar", 5, "Qodiriyning tili — asal. Har bir jumlasi she'rdek o'qiladi."),
    ('aziza', 'The Alchemist', 3.5, "Orzular ortidan borish haqida ilhomlantiruvchi kitob."),
    ('javohir', 'Sapiens: A Brief History of Humankind', 5, "Insoniyat tarixiga butunlay boshqacha nazar. Fikrlashni o'zgartiradi."),
    ('aziza', "Dunyoning ishlari", 5, "Har bir bobini yig'lamasdan o'qib bo'lmaydi. Dunyo onalari haqida eng zo'r asar."),
    ('javohir', 'Yulduzli tunlar', 5, "Boburning ichki kechinmalarini ajoyib tarzda ko'rsatib bergan. Tarixiy asarlar ichida durdona."),
    ('bekzod', 'Ikki eshik orasi', 5, "Qahramonlarning taqsiri juda fojiali bo'lsa-da, hayot haqiqatini ochib beradi."),
    ('aziza', 'Shum bola', 4.5, "Ajoyib kulgi va yumor bilan yozilgan, garchi qiyin davrlar haqida bo'lsa ham."),
    ('javohir', 'Animal Farm', 5, "Amazing critique of totalitarianism. Short but powerful."),
]

FAVORITES = [
    ('aziza', "O'tkan kunlar"),
    ('aziza', 'The Little Prince'),
    ('javohir', '1984'),
    ('javohir', 'Sapiens: A Brief History of Humankind'),
    ('bekzod', 'Crime and Punishment'),
    ('bekzod', "O'tkan kunlar"),
    ('aziza', "Dunyoning ishlari"),
    ('javohir', 'Yulduzli tunlar'),
    ('bekzod', 'Ikki eshik orasi'),
]

LIST_LIKES = [
    ('javohir', "Yuragimni zabt etgan kitoblar"),
    ('bekzod', "Yuragimni zabt etgan kitoblar"),
    ('aziza', "O'zbek adabiyoti durdonalari"),
    ('javohir', "O'zbek adabiyoti durdonalari"),
]

LIST_COMMENTS = [
    ('javohir', "Yuragimni zabt etgan kitoblar", "Zo'r tanlov! Kichkina shahzoda mening ham sevimlim."),
    ('aziza', "O'zbek adabiyoti durdonalari", "Ro'yxatga \"Sarob\"ni ham qo'shsangiz bo'lardi!"),
]

# kitob syujetini ochib yuboradigan taqrizlar
SPOILER_REVIEWS = [
    ('javohir', '1984'),
    ('bekzod', "O'tkan kunlar"),
]

REVIEW_COMMENTS = [
    ('javohir', 'aziza', "O'tkan kunlar", "To'liq qo'shilaman! Ayniqsa oxirgi boblari yig'latadi."),
    ('bekzod', 'aziza', "O'tkan kunlar", "Menga ham eng yoqqan asar."),
    ('aziza', 'javohir', '1984', "Men ham yaqinda o'qidim, hali ham ta'siridan chiqolmayapman."),
    ('aziza', 'bekzod', 'Crime and Punishment', "Sonya obrazlari haqida ko'proq yozsangiz bo'lardi!"),
]

QUESTIONS = [
    ('bekzod', "O'tkan kunlar", "Sizningcha, Otabek Zaynabga uylanishga rozi bo'lgani to'g'rimidi?",
     [('aziza', "Menimcha, u davr sharoitida boshqa iloji yo'q edi — ota-ona roziligi hamma narsadan ustun turgan.")]),
    ('aziza', '1984', "Winston oxirida haqiqatan ham Katta Og'ani sevib qoldimi yoki bu shunchaki taslim bo'lish edi?",
     [('javohir', "Menimcha, bu to'liq taslim bo'lish — Orwell aynan shu bilan umidsizlikni ko'rsatmoqchi bo'lgan.")]),
    ('javohir', 'The Alchemist', "Personal Legend (Shaxsiy Taqdir) tushunchasi real hayotda ishlaydimi?",
     []),
]

SHELF = [
    ('aziza', "O'tkan kunlar", 'read'),
    ('aziza', 'The Little Prince', 'read'),
    ('aziza', 'The Alchemist', 'read'),
    ('aziza', 'Kecha va kunduz', 'reading'),
    ('aziza', 'Sapiens: A Brief History of Humankind', 'want'),
    ('javohir', '1984', 'read'),
    ('javohir', "Harry Potter and the Philosopher's Stone", 'read'),
    ('javohir', 'Sapiens: A Brief History of Humankind', 'read'),
    ('javohir', 'Crime and Punishment', 'reading'),
    ('bekzod', 'Crime and Punishment', 'read'),
    ('bekzod', "O'tkan kunlar", 'read'),
    ('bekzod', 'Mehrobdan chayon', 'reading'),
    ('bekzod', 'The Great Gatsby', 'want'),
    ('aziza', 'Dunyoning ishlari', 'read'),
    ('aziza', 'Ikki eshik orasi', 'want'),
    ('javohir', 'Yulduzli tunlar', 'read'),
    ('javohir', 'Animal Farm', 'read'),
    ('bekzod', 'Ikki eshik orasi', 'read'),
    ('bekzod', 'Shum bola', 'read'),
]


DIARY = [
    # (user, kitob, boshlagan, tugatgan, baho, izoh)
    ('aziza', "O'tkan kunlar", date(2026, 5, 20), date(2026, 6, 2), 5, "Ikkinchi marta o'qishim — bu safar yanada ta'sirli bo'ldi."),
    ('aziza', 'The Little Prince', date(2026, 6, 18), date(2026, 6, 18), 5, "Bir kechada o'qib tugatdim."),
    ('aziza', 'The Alchemist', date(2026, 6, 24), date(2026, 7, 1), 4, ''),
    ('javohir', '1984', date(2026, 6, 1), date(2026, 6, 10), 5, "Ta'til boshlanishi bilan birinchi kitob."),
    ('javohir', 'Sapiens: A Brief History of Humankind', date(2026, 6, 15), date(2026, 7, 3), 5, "Har bir bobi alohida kashfiyot."),
    ('bekzod', 'Crime and Punishment', date(2026, 5, 25), date(2026, 6, 25), 5, "Bir oy davomida sekin, ta'mini his qilib o'qidim."),
    ('bekzod', "O'tkan kunlar", date(2026, 6, 28), date(2026, 7, 5), 5, ''),
    ('aziza', 'Dunyoning ishlari', date(2026, 7, 3), date(2026, 7, 6), 5, "Onamning sovg'asi bo'lgan kitobni yana bir bor o'qidim."),
    ('javohir', 'Yulduzli tunlar', date(2026, 6, 20), date(2026, 7, 5), 5, "Juda chuqur ma'noga ega."),
    ('bekzod', 'Ikki eshik orasi', date(2026, 6, 5), date(2026, 6, 20), 5, "Jurnalistlarning yozish uslubi ajoyib."),
]

READING_LISTS = [
    ('aziza', "Yuragimni zabt etgan kitoblar", "Qayta-qayta o'qigim keladigan asarlar",
     ["O'tkan kunlar", 'The Little Prince', 'The Alchemist']),
    ('javohir', 'Antiutopiya klassikasi', "O'ylashga majbur qiladigan distopiyalar",
     ['1984']),
    ('bekzod', "O'zbek adabiyoti durdonalari", "Har bir o'zbek o'qishi kerak bo'lgan asarlar",
     ["O'tkan kunlar", 'Mehrobdan chayon', 'Kecha va kunduz']),
]


class Command(BaseCommand):
    help = 'Demo ma\'lumotlar bilan bazani to\'ldiradi'

    def handle(self, *args, **options):
        genres = {name: Genre.objects.get_or_create(name=name)[0] for name in GENRES}

        books = {}
        for b in BOOKS:
            author, _ = Author.objects.update_or_create(
                name=b['author'], defaults={'bio': AUTHOR_BIOS.get(b['author'], '')}
            )
            book, created = Book.objects.get_or_create(
                title=b['title'],
                author=author,
                defaults={
                    'description': b['description'],
                    'published_year': b['year'],
                    'pages': b['pages'],
                    'cover_url': b['cover'],
                },
            )
            book.genres.set([genres[g] for g in b['genres']])
            if created:
                for name, role, desc in b['characters']:
                    Character.objects.create(book=book, name=name, role=role, description=desc)
            books[b['title']] = book

        users = {}
        for username, email, bio in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={'email': email, 'bio': bio}
            )
            if created:
                user.set_password('demo1234')
                user.save()
            users[username] = user

        # o'zaro obunalar
        pairs = [('aziza', 'javohir'), ('aziza', 'bekzod'), ('javohir', 'aziza'),
                 ('javohir', 'bekzod'), ('bekzod', 'aziza')]
        for f, t in pairs:
            Follow.objects.get_or_create(follower=users[f], following=users[t])

        for username, title, book_status in SHELF:
            item, created = ShelfItem.objects.get_or_create(
                user=users[username], book=books[title], defaults={'status': book_status}
            )
            if created:
                verb = {'want': Activity.SHELVED_WANT, 'reading': Activity.STARTED,
                        'read': Activity.FINISHED}[book_status]
                Activity.objects.create(user=users[username], verb=verb, book=books[title])

        for username, title, rating, text in REVIEWS:
            review, created = Review.objects.get_or_create(
                user=users[username], book=books[title],
                defaults={'rating': rating, 'text': text},
            )
            if created:
                Activity.objects.create(
                    user=users[username], verb=Activity.REVIEWED,
                    book=books[title], review=review,
                )
            elif review.rating != rating:
                review.rating = rating
                review.save()

        for username, title in FAVORITES:
            Favorite.objects.get_or_create(user=users[username], book=books[title])

        for username, title in SPOILER_REVIEWS:
            Review.objects.filter(user=users[username], book=books[title]).update(has_spoiler=True)

        for commenter, reviewer, title, text in REVIEW_COMMENTS:
            review = Review.objects.filter(user=users[reviewer], book=books[title]).first()
            if review:
                ReviewComment.objects.get_or_create(user=users[commenter], review=review, text=text)

        for liker, reviewer, title in LIKES:
            review = Review.objects.filter(user=users[reviewer], book=books[title]).first()
            if review:
                ReviewLike.objects.get_or_create(user=users[liker], review=review)

        for username, title, q_text, answers in QUESTIONS:
            question, created = Question.objects.get_or_create(
                user=users[username], book=books[title], text=q_text
            )
            if created:
                for a_user, a_text in answers:
                    Answer.objects.create(user=users[a_user], question=question, text=a_text)

        for username, title, d_start, d_end, rating, note in DIARY:
            entry, created = DiaryEntry.objects.get_or_create(
                user=users[username], book=books[title], date_read=d_end,
                defaults={'rating': rating, 'note': note, 'date_started': d_start},
            )
            if created:
                Activity.objects.create(
                    user=users[username], verb=Activity.LOGGED, book=books[title]
                )
            elif not entry.date_started:
                entry.date_started = d_start
                entry.save()

        lists_by_title = {}
        for username, title, desc, book_titles in READING_LISTS:
            rl, _ = ReadingList.objects.get_or_create(
                user=users[username], title=title, defaults={'description': desc}
            )
            lists_by_title[title] = rl
            for bt in book_titles:
                ReadingListItem.objects.get_or_create(reading_list=rl, book=books[bt])

        for username, title in LIST_LIKES:
            if title in lists_by_title:
                ListLike.objects.get_or_create(
                    user=users[username], reading_list=lists_by_title[title]
                )

        for username, title, text in LIST_COMMENTS:
            if title in lists_by_title:
                ListComment.objects.get_or_create(
                    user=users[username], reading_list=lists_by_title[title], text=text
                )

        # ---- Forum mavzulari ----
        forums = [
            ('aziza', "Eng yaxshi o'zbek romani qaysi?", None,
             "Sizningcha, o'zbek adabiyotining eng buyuk romani qaysi? Men \"O'tkan kunlar\" deb o'ylayman.",
             [('bekzod', "Albatta \"O'tkan kunlar\"! Qodiriy tengsiz."),
              ('javohir', "Menga \"Kecha va kunduz\" ham juda yoqadi.")]),
            ('javohir', 'Distopiya janrini yoqtiradiganlar shu yerga', None,
             "1984, Fahrenheit 451, Brave New World... Distopiya haqida gaplashamizmi? Qaysi biri sizni ko'proq o'ylantirgan?",
             [('aziza', "1984 — eng kuchlisi. Bugungi kun bilan juda mos.")]),
            ('bekzod', "\"O'tkan kunlar\" — Otabek va Kumush muhabbati", "O'tkan kunlar",
             "Bu asardagi eng ta'sirli sahna qaysi edi? Men uchun Kumushning o'limi.",
             [('aziza', "Yig'lagan edim o'sha joyda 😢"),
              ('javohir', "Qodiriyning tili shu qadar go'zalki...")]),
            ('aziza', '1984 — final haqida bahs (spoiler bor)', '1984',
             "Winstonning oxiri sizni qanoatlantirdimi? Menimcha, aynan shunday tugashi kerak edi.",
             [('bekzod', "Umidsiz, lekin haqiqiy. Orwell boshqacha yoza olmasdi.")]),
        ]
        for author, title, book_title, body, replies in forums:
            thread, created = ForumThread.objects.get_or_create(
                title=title,
                defaults={
                    'author': users[author],
                    'body': body,
                    'book': books.get(book_title) if book_title else None,
                },
            )
            if created:
                for r_user, r_text in replies:
                    ForumPost.objects.create(thread=thread, author=users[r_user], text=r_text)

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@badiiyat.uz', 'admin1234')
            self.stdout.write('Superuser: admin / admin1234')

        self.stdout.write(self.style.SUCCESS(
            f'Seed tugadi: {Book.objects.count()} kitob, {User.objects.count()} foydalanuvchi, '
            f'{Review.objects.count()} taqriz. Demo parol: demo1234'
        ))
