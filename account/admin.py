from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('phone_number', 'user_name', 'role', 'is_active',)
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('phone_number', 'user_name','role','u_type','email','full_name','is_active')}),
        ('Permissions', {'fields': ('is_admin', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('phone_number', 'role', 'password1', 'password2'),
    }),
    )

admin.site.register(User, CustomUserAdmin)

