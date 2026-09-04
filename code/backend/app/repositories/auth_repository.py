from typing import Any
from uuid import UUID

from app.models.base import utcnow
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.utils.bson import uuid_to_bin
from app.utils.mongo import raw_collection


class AuthRepository:
    async def create_refresh_token(self, rt: RefreshToken) -> RefreshToken:
        await rt.insert()
        return rt

    async def find_refresh_token(self, token_hash: str) -> RefreshToken | None:
        return await RefreshToken.find_one({"tokenHash": token_hash})

    async def delete_refresh_token(self, token_hash: str) -> None:
        rt = await RefreshToken.find_one({"tokenHash": token_hash})
        if rt:
            await rt.delete()

    async def revoke_all_refresh_tokens(self, user_id: UUID) -> int:
        result = await RefreshToken.find({"userId": user_id}).delete()
        return result.deleted_count if result else 0

    async def revoke_other_refresh_tokens(self, user_id: UUID, keep_token_hash: str) -> int:
        """Revoke all refresh tokens for the user except the given one.

        Used after a password change so the current session stays alive while
        every other device is signed out.
        """
        result = await RefreshToken.find(
            {"userId": user_id, "tokenHash": {"$ne": keep_token_hash}}
        ).delete()
        return result.deleted_count if result else 0

    async def create_password_reset_token(self, prt: PasswordResetToken) -> PasswordResetToken:
        await prt.insert()
        return prt

    async def find_and_delete_valid_reset_token(self, token_hash: str) -> dict[str, Any] | None:
        col = raw_collection(PasswordResetToken)
        doc = await col.find_one_and_delete(
            {"tokenHash": token_hash, "expiresAt": {"$gt": utcnow()}}
        )
        return doc

    async def replace_password_reset_token(
        self, user_id: UUID, new_token: PasswordResetToken
    ) -> None:
        col = raw_collection(PasswordResetToken)
        uid_bin = uuid_to_bin(user_id)
        new_id_bin = uuid_to_bin(new_token.id)
        token_id_bin = uuid_to_bin(new_token.user_id)
        doc: dict[str, Any] = {
            "_id": new_id_bin,
            "userId": token_id_bin,
            "tokenHash": new_token.token_hash,
            "expiresAt": new_token.expires_at,
            "createdAt": new_token.created_at,
        }
        await col.find_one_and_replace(
            {"userId": uid_bin},
            doc,
            upsert=True,
        )
