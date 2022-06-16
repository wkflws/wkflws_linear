import json
from typing import Any, Optional
from urllib.parse import urlparse

from wkflws.events import Event
from wkflws.http import http_method, Request
from wkflws.logging import getLogger
from wkflws.triggers.webhook import WebhookTrigger

from . import __identifier__, __version__

logger = getLogger("wkflws_linear.trigger")
logger.setLevel(10)


async def process_webhook_request(request: Request) -> Optional[Event]:
    """Accept and process an HTTP request returning a event for the bus."""
    url = urlparse(request.url)
    webhook_id = url.path.split("/")[2]
    identifier = request.headers["linear-delivery"]

    metadata = request.headers.copy()
    metadata["linear_webhook_id"] = webhook_id

    data = json.loads(request.body)
    from pprint import pformat

    logger.debug(pformat(data))
    return Event(identifier, metadata, data)


async def accept_event(event: Event) -> tuple[Optional[str], dict[str, Any]]:
    """Accept and process data from the event bus."""

    event_type = event.metadata["linear-event"]
    initial_node = None

    match event_type:
        case "Issue":
            initial_node = "wkflws_linear.triggers.issue"
        case "Issue attachments":
            initial_node = "wkflws_linear.triggers.issue_attachments"
        case "Issue comments":
            initial_node = "wkflws_linear.triggers.issue_comments"
        case "Comment reaction":
            initial_node = "wkflws_linear.triggers.comment_reaction"
        case "Projects":
            initial_node = "wkflws_linear.triggers.projects"
        case "Cycles":
            initial_node = "wkflws_linear.triggers.cycles"
        case "Issue labels":
            initial_node = "wkflws_linear.triggers.issue_labels"
        case _:
            logger.error(
                f"Received unsupported Linear event type '{event_type}' "
                f"(id:{event.identifier}"
            )
            return None, {}

    return initial_node, event.data


webhook = WebhookTrigger(
    client_identifier=__identifier__,
    client_version=__version__,
    process_func=accept_event,
    routes=(
        (
            (http_method.POST,),
            "/linear/{webhook_id}/",
            process_webhook_request,
        ),
    ),
)
