from django.contrib import admin

from .models import (
    Activity,
    Answer,
    DiaryEntry,
    Question,
    ReadingChallenge,
    ReadingList,
    ReadingListItem,
    Review,
    ShelfItem,
)

admin.site.register(Review)
admin.site.register(ShelfItem)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Activity)
admin.site.register(DiaryEntry)
admin.site.register(ReadingList)
admin.site.register(ReadingListItem)
admin.site.register(ReadingChallenge)
