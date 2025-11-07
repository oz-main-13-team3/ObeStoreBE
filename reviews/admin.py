from django.contrib import admin

from .models import Keyword, Review, ReviewImage, ReviewKeyword


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1


class ReviewKeywordInline(admin.TabularInline):
    model = ReviewKeyword
    extra = 1


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "review_title", "user", "product", "created_at")
    search_fields = ("review_title", "content")
    list_filter = ("created_at",)
    inlines = [ReviewImageInline, ReviewKeywordInline]


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    pass
