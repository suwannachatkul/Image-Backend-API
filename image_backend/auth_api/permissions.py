from rest_framework import permissions

class AdminPermission(permissions.BasePermission):
    required_groups = ['admin']

    def has_permission(self, request, view):
        return bool(request.user.groups.filter(name__in=self.required_groups))

class UserPermission(permissions.BasePermission):
    required_groups = ['admin', 'user']

    def has_permission(self, request, view):
        return bool(request.user.groups.filter(name__in=self.required_groups))

class GuestPermission(permissions.BasePermission):
    required_groups = ['admin', 'user', 'guest']

    def has_permission(self, request, view):
        return bool(request.user.groups.filter(name__in=self.required_groups))
