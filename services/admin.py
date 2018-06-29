from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin

from .models import Service


@admin.register(Service)
class ServiceAdmin(TranslatableAdmin):
    list_display = ('name', 'url', 'application', 'client')

    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'description'),
        }),
        (_('Not translatable fields'), {
            'fields': ('image', 'application', 'client')
        }),
    )

    """
    def save_model(self, request, obj, form, change):
        if obj.description == '':
            obj.description = None  # for some reason Django saves empty nullable TextField as ''
        super().save_model(request, obj, form, change)
    """
