
from django import forms

from crispy_forms.layout import Layout, Fieldset

from core.utils import horizontal_form_helper, indented_without_label
from labour.forms import AlternativeFormMixin
from labour.models import Signup, JobCategory, WorkPeriod

from .models import SignupExtra


class SignupExtraForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SignupExtraForm, self).__init__(*args, **kwargs)
        self.helper = horizontal_form_helper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset('Lisätiedot',
                'special_diet',
                'special_diet_other',
                'prior_experience',
                'y_u',
                'free_text',
                indented_without_label('want_certificate'),
            )
        )

    class Meta:
        model = SignupExtra
        fields = (
            'special_diet',
            'special_diet_other',
            'prior_experience',
            'y_u',
            'free_text',
            'want_certificate',
        )

        widgets = dict(
            special_diet=forms.CheckboxSelectMultiple,
        )


class OrganizerSignupForm(forms.ModelForm, AlternativeFormMixin):
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        admin = kwargs.pop('admin')

        assert not admin

        super(OrganizerSignupForm, self).__init__(*args, **kwargs)

        self.helper = horizontal_form_helper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset('Tehtävän tiedot',
                'job_title',
            ),
        )

        self.fields['job_title'].help_text = "Mikä on tehtäväsi vastaavana? Printataan badgeen."
        self.fields['job_title'].required = True

    class Meta:
        model = Signup
        fields = ('job_title',)

    def get_excluded_m2m_field_defaults(self):
        return dict(
            job_categories=JobCategory.objects.filter(event__slug='popcult2020', name='Vastaava'),
        )


class OrganizerSignupExtraForm(forms.ModelForm, AlternativeFormMixin):
    def __init__(self, *args, **kwargs):
        super(OrganizerSignupExtraForm, self).__init__(*args, **kwargs)
        self.helper = horizontal_form_helper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset('Lisätiedot',
                'special_diet',
                'special_diet_other',
            ),
        )


    class Meta:
        model = SignupExtra
        fields = (
            'special_diet',
            'special_diet_other',
        )

        widgets = dict(
            special_diet=forms.CheckboxSelectMultiple,
        )

    def get_excluded_field_defaults(self):
        return dict(
            free_text='Syötetty käyttäen vastaavan ilmoittautumislomaketta',
        )

    def get_excluded_m2m_field_defaults(self):
        return dict()


class ProgrammeSignupExtraForm(forms.ModelForm, AlternativeFormMixin):
    def __init__(self, *args, **kwargs):
        super(ProgrammeSignupExtraForm, self).__init__(*args, **kwargs)
        self.helper = horizontal_form_helper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'special_diet',
            'special_diet_other',
        )


    class Meta:
        model = SignupExtra
        fields = (
            'special_diet',
            'special_diet_other',
        )

        widgets = dict(
            special_diet=forms.CheckboxSelectMultiple,
        )

    def get_excluded_field_defaults(self):
        return dict(
            free_text='Syötetty käyttäen ohjelmanjärjestäjän ilmoittautumislomaketta',
        )

    def get_excluded_m2m_field_defaults(self):
        return dict()
