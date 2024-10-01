from djstripe import webhooks
from djstripe.models import Customer, Event, Subscription

from core.models import Profile
from osig.utils import get_osig_logger

logger = get_osig_logger(__name__)


@webhooks.handler("customer.subscription.created")
def handle_created_subscription(**kwargs):
    event_id = kwargs["event"].id
    event = Event.objects.get(id=event_id)

    customer = Customer.objects.get(id=event.data["object"]["customer"])
    subscription = Subscription.objects.get(id=event.data["object"]["id"])

    profile = Profile.objects.get(customer=customer)
    profile.subscription = subscription
    profile.save(update_fields=["subscription"])
