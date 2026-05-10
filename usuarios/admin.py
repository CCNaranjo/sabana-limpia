from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('email', 'rol', 'municipio', 'is_staff', 'date_joined')
    list_filter   = ('rol', 'municipio', 'is_staff')
    search_fields = ('email',)
    ordering      = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('SabanaLimpia', {'fields': ('rol', 'municipio')}),
    )