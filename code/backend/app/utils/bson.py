from uuid import UUID

from bson.binary import Binary, UuidRepresentation


def uuid_to_bin(uid: UUID) -> Binary:
    """Convert a Python UUID to a BSON Binary for raw pymongo queries."""
    return Binary.from_uuid(uid, uuid_representation=UuidRepresentation.STANDARD)


def bin_to_uuid(bin_value) -> UUID | None:
    """Convert a BSON Binary (from aggregation results) back to a Python UUID."""
    if isinstance(bin_value, Binary):
        return bin_value.as_uuid(uuid_representation=UuidRepresentation.STANDARD)
    if isinstance(bin_value, UUID):
        return bin_value
    return None
