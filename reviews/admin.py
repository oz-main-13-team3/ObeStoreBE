from django.contrib import admin

from .models import Review, Keyword, ReviewImage, ReviewKeyword


# Register your models here.
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ("id", "review_title", "user", "product", "created_at")
	search_fields = ("review_title", "content")
	list_filter = ('created_at',)
