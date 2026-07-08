from django.contrib import admin

from .models import ForumPost, ForumThread


class ForumPostInline(admin.TabularInline):
    model = ForumPost
    extra = 0


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'book', 'last_activity')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ForumPostInline]


admin.site.register(ForumPost)
