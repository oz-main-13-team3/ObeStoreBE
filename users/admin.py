from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User, Address, Point


class MyUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "username", "nickname", "phone_number")


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("email", "username", "nickname", "phone_number", "status", "is_staff", "is_superuser", "groups", "user_permissions")

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ("address_name", "recipient", "recipient_phone", "post_code", "address", "detail_address", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    show_change_link = True
    ordering = ("updated_at",)

class PointInline(admin.TabularInline):
    model = Point
    extra = 0
    fields = ("balance", "amount", "created_at", "updated_at")
    readonly_fields = ("balance", "amount", "created_at", "updated_at")
    can_delete = False
    ordering = ("updated_at", "-id")

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = MyUserCreationForm
    form = MyUserChangeForm
    model = User
    inlines = [AddressInline, PointInline]

    list_display = ("id", "email", "username", "nickname", "phone_number", "status", "is_active", "is_staff", "is_superuser", "created_at", "updated_at")
    list_filter = ("status", "is_staff", "is_superuser", "groups")
    search_fields = ("email", "username", "nickname", "phone_number")
    ordering = ("id",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("기본 정보", {
            "fields": ("email", "username", "nickname", "phone_number", "password")
        }),
        ("권한", {
            "fields": ("status", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("기타", {
            "fields": ("last_login", "created_at", "updated_at")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "username",
                "nickname",
                "phone_number",
                "password1",
                "password2",
                "status",
                "is_staff",
                "is_superuser",
                "groups",
            ),
        }),
    )
    filter_horizontal = ("groups", "user_permissions")

    @admin.action(description="선택한 사용자를 활성화(active)로 변경")
    def mark_active(self, request, queryset):
        updated = queryset.update(status="active")
        self.message_user(request, f"{updated}명의 사용자가 활성화되었습니다.")

    @admin.action(description="선택한 사용자를 비활성화(ready)로 변경")
    def mark_ready(self, request, queryset):
        updated = queryset.update(status="ready")
        self.message_user(request, f"{updated}명의 사용자가 비활성화(ready)되었습니다.")

    @admin.action(description="선택한 사용자를 휴면(dormancy)으로 변경")
    def mark_dormancy(self, request, queryset):
        updated = queryset.update(status="dormancy")
        self.message_user(request, f"{updated}명의 사용자가 휴면 처리되었습니다.")

    actions = ("mark_active", "mark_ready", "mark_dormancy",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "address_name", "recipient", "recipient_phone", "post_code", "address", "detail_address", "created_at", "updated_at")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
    list_select_related = ("user",)
    readonly_fields = ()

@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "balance", "amount", "created_at", "updated_at")
    search_fields = ("user__email",)
    list_select_related = ("user",)
    autocomplete_fields = ("user",)

    readonly_fields = ("user", "balance", "amount", "created_at", "updated_at")

    # 수동으로 포인트 추가 금지
    def has_add_permission(self, request):
        return False
    # 포인트 수정 금지
    def has_change_permission(self, request, obj=None):
        return False
    # 포인트 삭제 금지
    def has_delete_permission(self, request, obj=None):
        return False
