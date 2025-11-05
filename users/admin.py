from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User

class MyUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "username", "nickname", "phone_number")


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("email", "username", "nickname", "phone_number", "status", "is_staff", "is_superuser", "groups", "user_permissions")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = MyUserCreationForm
    form = MyUserChangeForm
    model = User

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
            "fields": ("status", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")
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

    # 다중 선택 UI (그룹/권한)
    filter_horizontal = ("groups", "user_permissions")

    # [액션] 리스트에서 체크된 유저들을 일괄 상태 변경
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