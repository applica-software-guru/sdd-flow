import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_notification_service
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.notifications import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
)
from app.services.notifications import (
    SUPPORTED_EVENT_TYPES,
    NotificationService,
    default_email_enabled,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    items, total = await svc.list_notifications_for_user(
        current_user.id, unread_only=unread_only, page=page, page_size=page_size
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    notification = await svc.mark_notification_read(notification_id, current_user.id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    return {"count": await svc.unread_notification_count(current_user.id)}


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> dict[str, str]:
    await svc.mark_all_notifications_read(current_user.id)
    return {"detail": "All notifications marked as read"}


# ---------------------------------------------------------------------------
# Email notification preferences
# ---------------------------------------------------------------------------


@router.get("/preferences", response_model=list[NotificationPreferenceResponse])
async def get_preferences(
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> list[NotificationPreferenceResponse]:
    """Email preferences for every supported event type.

    Stored records are merged with defaults (comment_added on, others off)
    so clients always receive one entry per event type.
    """
    stored = await svc.get_email_preferences(current_user.id)
    return [
        NotificationPreferenceResponse(
            event_type=event_type,
            email_enabled=stored.get(event_type, default_email_enabled(event_type)),
        )
        for event_type in SUPPORTED_EVENT_TYPES
    ]


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preference(
    body: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceResponse:
    """Upsert the email preference for one event type."""
    pref = await svc.upsert_email_preference(current_user.id, body.event_type, body.email_enabled)
    return NotificationPreferenceResponse(
        event_type=pref.event_type, email_enabled=pref.email_enabled
    )
