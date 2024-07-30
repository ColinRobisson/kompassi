from .models import Event, Organization
from .page_wizard import page_wizard_clear

NEVER_BLOW_PAGE_WIZARD_PREFIXES = [
    # we have addresses like /desuprofile/confirm/475712413a0ddc3c7a57c6721652b75449bf3c89
    # that should not blow the page wizard when used within a signup page wizard flow
    "/desuprofile/confirm/",
    "/oauth2/",
    "/oidc/",
]


class PageWizardMiddleware:
    """
    MIDDLEWARE = (
        # ...

        'core.middleware.page_wizard_middleware'
    )

    Clear the page wizard when visiting a non-related page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def _should_clear_page_wizard(self, request) -> bool:
        related = request.session.get("core.utils.page_wizard.related", None)
        if related is None:
            return False
        if request.method != "GET":
            return False
        if request.path in related:
            return False

        return any(request.path.startswith(prefix) for prefix in NEVER_BLOW_PAGE_WIZARD_PREFIXES)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if self._should_clear_page_wizard(request):
            page_wizard_clear(request)


class EventOrganizationMiddleware:
    """
    Sets request.event and request.organization if they can be deduced from the URL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.event = None
        request.organization = None

        if resolver_match := request.resolver_match:
            if event_slug := resolver_match.kwargs.get("event_slug"):
                if event := Event.objects.filter(slug=event_slug).select_related("organization").first():
                    request.event = event
                    request.organization = event.organization
            elif organization_slug := resolver_match.kwargs.get("organization_slug"):
                request.organization = Organization.objects.filter(slug=organization_slug).first()
