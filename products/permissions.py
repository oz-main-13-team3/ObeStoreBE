from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # 읽기는 모두 허용
        if request.method in permissions.SAFE_METHODS:
            return True
        # 작성자이거나 관리자이면 허용
        return obj.user == request.user or request.user.is_staff
