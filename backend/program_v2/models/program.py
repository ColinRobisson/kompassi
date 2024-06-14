from __future__ import annotations

import logging
from itertools import batched
from typing import TYPE_CHECKING, Self

from django.conf import settings
from django.db import models, transaction
from django.http import HttpRequest
from django.urls import reverse

from core.models import Event
from core.utils import validate_slug

if TYPE_CHECKING:
    from programme.models.programme import Programme

    from .dimension import ProgramDimensionValue
    from .meta import ProgramV2EventMeta
    from .schedule import ScheduleItem


logger = logging.getLogger("kompassi")


class Program(models.Model):
    id: int

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="programs")
    title = models.CharField(max_length=1023)
    slug = models.CharField(max_length=1023, validators=[validate_slug])
    description = models.TextField(blank=True)
    other_fields = models.JSONField(blank=True, default=dict)

    favorited_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="favorite_programs", blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # denormalized fields
    cached_dimensions = models.JSONField(default=dict)
    cached_earliest_start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "The earliest start time of any schedule item of this program. "
            "NOTE: This is not the same as the program's start time. "
            "The intended purpose of this field is to exclude programs that have not yet started. "
            "Always use `scheduleItems` for the purpose of displaying program times."
        ),
    )
    cached_latest_end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "The latest end time of any schedule item of this program. "
            "NOTE: This is not the same as the program's start end. "
            "The intended purpose of this field is to exclude programs that have already ended. "
            "Always use `scheduleItems` for the purpose of displaying program times."
        ),
    )
    cached_location = models.JSONField(blank=True, default=dict)
    cached_color = models.CharField(max_length=15, blank=True, default="")

    # related fields
    dimensions: models.QuerySet[ProgramDimensionValue]
    schedule_items: models.QuerySet[ScheduleItem]

    class Meta:
        unique_together = ("event", "slug")

    def __str__(self):
        return str(self.title)

    def refresh_cached_fields(self):
        self.refresh_cached_dimensions()
        self.refresh_cached_times()

    @classmethod
    def refresh_cached_fields_qs(cls, queryset: models.QuerySet[Self]):
        cls.refresh_cached_dimensions_qs(queryset)
        cls.refresh_cached_times_qs(queryset)

    def _build_dimensions(self):
        """
        Used to populate cached_dimensions
        """
        # TODO should all event dimensions always be present, or only those with values?
        # TODO when dimensions are changed for an event, refresh all cached_dimensions
        dimensions = {dimension.slug: [] for dimension in self.event.program_dimensions.all()}
        for pdv in self.dimensions.all():
            dimensions[pdv.dimension.slug].append(pdv.value.slug)
        return dimensions

    def _build_location(self):
        localized_locations: dict[str, set[str]] = {}

        if location_dimension := self.meta.location_dimension:
            for pdv in self.dimensions.filter(dimension=location_dimension):
                for lang, title in pdv.value.title.items():
                    if not title:
                        # placate typechecker
                        continue

                    localized_locations.setdefault(lang, set()).add(title)

        return {lang: ", ".join(locations) for lang, locations in localized_locations.items() if locations}

    def _get_color(self):
        """
        Gets a color for the program from its dimension values.
        TODO deterministic behaviour when multiple colors are present (ordering for dimensions/values?)
        """
        first_pdv_with_color = self.dimensions.exclude(value__color="").first()
        return first_pdv_with_color.value.color if first_pdv_with_color else ""

    def refresh_cached_dimensions(self):
        from .schedule import ScheduleItem

        self.cached_dimensions = self._build_dimensions()
        self.cached_location = self._build_location()
        self.cached_color = self._get_color()
        self.save(update_fields=["cached_dimensions", "cached_location", "cached_color"])
        self.schedule_items.update(cached_location=self.cached_location)

        bulk_update_schedule_items = []
        for schedule_item in self.schedule_items.filter(program=self).select_for_update(of=("self",)):
            schedule_item.cached_location = self.cached_location
            bulk_update_schedule_items.append(schedule_item)
        ScheduleItem.objects.bulk_update(bulk_update_schedule_items, ["cached_location"])

    program_batch_size = 100
    schedule_item_batch_size = 100

    @classmethod
    def refresh_cached_dimensions_qs(cls, queryset: models.QuerySet[Self]):
        from .schedule import ScheduleItem

        with transaction.atomic():
            for page, program_batch in enumerate(
                batched(
                    queryset.select_for_update(of=("self",)).only(
                        "id",
                        "cached_dimensions",
                        "cached_location",
                        "cached_color",
                    ),
                    cls.program_batch_size,
                )
            ):
                logger.info("Refreshing cached dimensions for programs, page %d", page)
                bulk_update_programs = []
                for program in program_batch:
                    program.cached_dimensions = program._build_dimensions()
                    program.cached_location = program._build_location()
                    program.cached_color = program._get_color()
                    bulk_update_programs.append(program)
                cls.objects.bulk_update(bulk_update_programs, ["cached_dimensions", "cached_location", "cached_color"])

            for page, schedule_item_batch in enumerate(
                batched(
                    ScheduleItem.objects.filter(program__in=queryset)
                    .select_for_update(of=("self",))
                    .select_related("program")
                    .only("program__cached_location"),
                    cls.schedule_item_batch_size,
                )
            ):
                logger.info("Refreshing cached locations for schedule items, page %d", page)
                bulk_update_schedule_items = []
                for schedule_item in schedule_item_batch:
                    schedule_item.cached_location = schedule_item.program.cached_location
                    bulk_update_schedule_items.append(schedule_item)
                ScheduleItem.objects.bulk_update(bulk_update_schedule_items, ["cached_location"])

        logger.info("Finished refreshing cached dimensions for programs")

    def refresh_cached_times(self):
        """
        Used to populate cached_earliest_start_time and cached_latest_end_time
        """
        earliest_start_time = self.schedule_items.order_by("start_time").first()
        latest_end_time = self.schedule_items.order_by("cached_end_time").last()

        self.cached_earliest_start_time = earliest_start_time.start_time if earliest_start_time else None
        self.cached_latest_end_time = latest_end_time.cached_end_time if latest_end_time else None

        self.save(update_fields=["cached_earliest_start_time", "cached_latest_end_time"])

    @classmethod
    def refresh_cached_times_qs(cls, queryset: models.QuerySet[Self]):
        with transaction.atomic():
            for page, batch in enumerate(
                batched(
                    queryset.select_for_update(of=("self",)).only(
                        "id",
                        "cached_earliest_start_time",
                        "cached_latest_end_time",
                    ),
                    cls.program_batch_size,
                )
            ):
                logger.info("Refreshing cached times for programs, page %d", page)
                bulk_update = []
                for program in batch:
                    earliest_start_time = program.schedule_items.order_by("start_time").first()
                    latest_end_time = program.schedule_items.order_by("cached_end_time").last()

                    program.cached_earliest_start_time = earliest_start_time.start_time if earliest_start_time else None
                    program.cached_latest_end_time = latest_end_time.cached_end_time if latest_end_time else None

                    bulk_update.append(program)
                cls.objects.bulk_update(bulk_update, ["cached_earliest_start_time", "cached_latest_end_time"])

        logger.info("Finished refreshing cached times for programs")

    @classmethod
    def import_program_from_v1(
        cls,
        event: Event,
        queryset: models.QuerySet[Programme] | None = None,
        clear: bool = False,
    ):
        from programme.models.programme import Programme

        if (meta := event.program_v2_event_meta) is None:
            raise ValueError(f"Event {event.slug} does not have program_v2_event_meta")

        if queryset is None:
            queryset = Programme.objects.filter(category__event=event)

        Importer = meta.importer_class
        importer = Importer(event=event)

        importer.import_dimensions(clear=clear, refresh_cached_dimensions=False)
        return importer.import_program(queryset, clear=clear)

    @property
    def meta(self) -> ProgramV2EventMeta:
        if (meta := self.event.program_v2_event_meta) is None:
            raise TypeError(f"Event {self.event.slug} does not have program_v2_event_meta but Programs are present")

        return meta

    def get_calendar_export_link(self, request: HttpRequest):
        return request.build_absolute_uri(
            reverse(
                "program_v2:single_program_calendar_export_view",
                kwargs=dict(
                    event_slug=self.event.slug,
                    program_slug=self.slug,
                ),
            )
        )
