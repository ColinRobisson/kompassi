from collections import namedtuple

from django.db import models

from core.models import EventMetaBase, Person
from labour.models import Signup


UnassignedOrganizer = namedtuple('UnassignedOrganizer', 'person signup')


class IntraEventMeta(EventMetaBase):
    organizer_group = models.ForeignKey('auth.Group', related_name='as_organizer_group_for_intra_event_meta')

    @classmethod
    def get_or_create_dummy(cls):
        from core.models import Event
        event, unused = Event.get_or_create_dummy()
        admin_group, organizer_group = cls.get_or_create_groups(event, ['admins', 'organizers'])
        return cls.objects.get_or_create(event=event, defaults=dict(
            admin_group=admin_group,
            organizer_group=organizer_group,
        ))

    def is_user_organizer(self, user):
        return self.is_user_in_group(user, self.organizer_group)

    def is_user_allowed_to_access(self, user):
        return user.is_authenticated() and (
            user.is_superuser or
            self.is_user_organizer(user) or
            self.is_user_admin(user)
        )

    @property
    def unassigned_organizers(self):
        if not hasattr(self, '_unassigned_organizers'):
            self._unassigned_organizers = [
                UnassignedOrganizer(
                    person=person,
                    signup=Signup.objects.get(event=self.event, person=person)
                )

                for person in Person.objects.filter(
                    user__groups=self.organizer_group,
                ).exclude(
                    user__person__team_memberships__team__event_id=self.event.id,
                )
            ]

        return self._unassigned_organizers
