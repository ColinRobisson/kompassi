# encoding: utf-8

from django.contrib import admin
from django.conf import settings

from .models import Event, Person, Venue


class PersonAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Basic information', {'fields': [('first_name', 'surname'), 'nick']}),
        ('Contact information', {'fields': ['email', 'phone']}),
        ('Display', {'fields': ['preferred_name_display_style']}),
        ('Notes', {'fields': ['notes']}),
    ]

    list_display = ('surname', 'first_name', 'nick', 'email', 'phone', 'username')
    search_fields = ('surname', 'first_name', 'nick', 'email', 'user__username')
    ordering = ('surname', 'first_name', 'nick')


extra_inlines = []

if 'labour' in settings.INSTALLED_APPS:
    from labour.admin import InlineLabourEventMetaAdmin
    extra_inlines.append(InlineLabourEventMetaAdmin)

if 'programme' in settings.INSTALLED_APPS:
    from programme.admin import InlineProgrammeEventMetaAdmin
    extra_inlines.append(InlineProgrammeEventMetaAdmin)

if 'tickets' in settings.INSTALLED_APPS:
    from tickets.admin import InlineTicketsEventMetaAdmin
    extra_inlines.append(InlineTicketsEventMetaAdmin)


class EventAdmin(admin.ModelAdmin):
    inlines = tuple(extra_inlines)

    fieldsets = (
        ('Tapahtuman nimi', dict(fields=(
            'name',
            'name_genitive',
            'name_illative',
            'name_inessive',
            'slug'
        ))),

        ('Tapahtuman perustiedot', dict(fields=(
            'venue',
            'start_time',
            'end_time',
        ))),

        ('Järjestäjän tiedot', dict(fields=(
            'homepage_url',
            'organization_name',
            'organization_url',
        ))),
    )

    def get_readonly_fields(self, request, obj=None):
        # slug may be edited when creating but not when modifying existing event
        # (breaks urls and kills puppies)
        if obj:
            return self.readonly_fields + ('slug',)

        return self.readonly_fields


admin.site.register(Event, EventAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Venue)
