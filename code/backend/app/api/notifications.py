import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_user
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.repositories import NotificationRepository
from app.schemas.notifications import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
)
from app.services.collab_notifications import (
    SUPPORTED_EVENT_TYPES,
    default_email_enabled,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    notification_repo = NotificationRepository()
    items, total = await notification_repo.find_by_user(
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
):
    notification_repo = NotificationRepository()
    notification = await notification_repo.mark_read(notification_id, current_user.id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


@router.get("/unread-count")
async def unread_count(current_user: User = Depends(get_current_user)):
    notification_repo = NotificationRepository()
    _, total = await notification_repo.find_by_user(
        current_user.id, unread_only=True, page=1, page_size=1
    )
    return {"count": total}


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
):
    notification_repo = NotificationRepository()
    await notification_repo.mark_all_read(current_user.id)
    return {"detail": "All notifications marked as read"}


# ---------------------------------------------------------------------------
# Email notification preferences
# ---------------------------------------------------------------------------


@router.get("/preferences", response_model=list[NotificationPreferenceResponse])
async def get_preferences(
    current_user: User = Depends(get_current_user),
):
    """Email preferences for every supported event type.

    Stored records are merged with defaults (comment_added on, others off)
    so clients always receive one entry per event type.
    """
    prefs = await NotificationPreference.find({"userId": current_user.id}).to_list()
    stored = {p.event_type: p.email_enabled for p in prefs}
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
):
    """Upsert the email preference for one event type."""
    if body.event_type not in SUPPORTED_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported event type. Supported: {', '.join(SUPPORTED_EVENT_TYPES)}",
        )

    pref = await NotificationPreference.find_one(
        {"userId": current_user.id, "eventType": body.event_type}
    )
    if pref is None:
        pref = NotificationPreference(
            user_id=current_user.id,
            event_type=body.event_type,
            email_enabled=body.email_enabled,
        )
        await pref.insert()
    else:
        pref.email_enabled = body.email_enabled
        await pref.save()

    return NotificationPreferenceResponse(
        event_type=pref.event_type, email_enabled=pref.email_enabled
    )
