from django.contrib import admin

from .models import Author, Book, Character, Genre


class CharacterInline(admin.TabularInline):
    model = Character
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_year')
    search_fields = ('title', 'author__name')
    list_filter = ('genres',)
    inlines = [CharacterInline]
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Character)
