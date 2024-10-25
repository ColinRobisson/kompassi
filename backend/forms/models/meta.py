from dataclasses import dataclass

from core.models.event import Event
from core.models.event_meta_base import EventMetaBase
from core.models.person import Person


class FormsEventMeta(EventMetaBase):
    """
    The existence of a FormsEventMeta enables giving privileges to users to manage forms
    from the Intra privileges view. It does not feature gate the actual form management
    interface: if someone has CBAC privileges to that, they will be able to access it
    regardless of the existence of a FormsEventMeta.
    """

    use_cbac = True


@dataclass
class FormsEventMetaPlaceholder:
    """
    This is what GraphQL uses to facilitate the above.
    TODO perhaps remove and create FormsEventMeta for all events using Forms?
    """

    event: Event


@dataclass
class FormsProfileMeta:
    """
    No need for an actual model for now. This serves as a stand-in for GraphQL.
    """

    person: Person
