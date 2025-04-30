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
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "password1", "password2","first_name","last_name"),
            },
        ),
    )