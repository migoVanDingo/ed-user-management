# platform_common/pubsub/user_events.py

from typing import Optional

from platform_common.pubsub.factory import get_publisher
from platform_common.pubsub.event import PubSubEvent

CHANNEL_USER_CHANGES = "user:changes"


async def publish_user_verified_event(
    user_id: str,
    organization_id: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
) -> None:
    """
    Publish a 'user_verified' event to the user:changes channel.

    The datastore service subscribes to this and will create the default
    datastore (idempotently) for this user.
    """
    publisher = get_publisher()

    event = PubSubEvent(
        event_type="user_verified",  # <- matches key in datastore subscriber
        payload={
            "user_id": user_id,
            "organization_id": organization_id,
            "email": email,
            "username": username,
        },
    )

    await publisher.publish(CHANNEL_USER_CHANGES, event)
