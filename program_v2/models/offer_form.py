from typing import Optional


from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from localized_fields.models import LocalizedModel
from localized_fields.fields import LocalizedTextField

from core.utils import NONUNIQUE_SLUG_FIELD_PARAMS
from forms.models.form import EventForm


class OfferForm(LocalizedModel):
    event = models.ForeignKey("core.Event", on_delete=models.CASCADE, related_name="program_offer_forms")
    slug = models.CharField(**NONUNIQUE_SLUG_FIELD_PARAMS)  # type: ignore

    short_description = LocalizedTextField(
        blank=True,
        default=dict,
        verbose_name=_("short description"),
        help_text=_("Visible on the page that offers different kinds of forms."),
    )

    languages = models.ManyToManyField(
        "forms.EventForm",
        verbose_name=_("language versions"),
        help_text=_(
            "The form will be available in these languages. "
            "Each language can have its own set of fields. "
            "There must be exactly one form per supported language."
        ),
    )

    def get_form(self, requested_language: str) -> Optional[EventForm]:
        try:
            return self.languages.get(language=requested_language)
        except EventForm.DoesNotExist:
            pass

        for language, _ in settings.LANGUAGES:
            if language == requested_language:
                # already tried above, skip one extra query
                continue

            try:
                return self.languages.get(language=language)
            except EventForm.DoesNotExist:
                pass

        raise EventForm.DoesNotExist()

    class Meta:
        unique_together = [
            ("event", "slug"),
        ]