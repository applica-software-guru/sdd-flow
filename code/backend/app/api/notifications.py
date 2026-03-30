import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.repositories import NotificationRepository
from app.schemas.notifications import NotificationListResponse, NotificationResponse

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
