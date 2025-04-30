from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
# from core.models import Customer


# class CustomerInline(admin.StackedInline):
#     model = Customer
#     extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # inlines = [CustomerInline]

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "password1", "password2","first_name","last_name"),
            },
        ),
    )
    ordering = ('phone',)
    list_display = ('phone', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name',)
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'groups')