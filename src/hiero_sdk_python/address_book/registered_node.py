"""Immutable registered node model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.hapi.services.state.addressbook.registered_node_pb2 import (
    RegisteredNode as RegisteredNodeProto,
)
from hiero_sdk_python.utils.key_utils import key_to_proto


@dataclass(frozen=True)
class RegisteredNode:
    """An immutable registered node from network state."""

    MAX_DESCRIPTION_BYTES: ClassVar[int] = 100

    registered_node_id: int
    admin_key: Key | None = None
    description: str | None = None
    service_endpoints: tuple[RegisteredServiceEndpoint, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate immutable registered-node state."""
        if self.description is not None and len(self.description.encode("utf-8")) > self.MAX_DESCRIPTION_BYTES:
            raise ValueError("description must not exceed 100 UTF-8 bytes.")

    def _to_proto(self) -> RegisteredNodeProto:
        """Convert the registered node to protobuf."""
        return RegisteredNodeProto(
            registered_node_id=self.registered_node_id,
            admin_key=key_to_proto(self.admin_key),
            description=self.description,
            service_endpoint=[endpoint._to_proto() for endpoint in self.service_endpoints],
        )

    @classmethod
    def _from_proto(cls, proto: RegisteredNodeProto) -> RegisteredNode:
        """Build a registered node from protobuf."""
        return cls(
            registered_node_id=proto.registered_node_id,
            admin_key=Key.from_proto_key(proto.admin_key) if proto.HasField("admin_key") else None,
            description=proto.description or None,
            service_endpoints=tuple(
                RegisteredServiceEndpoint._from_proto(endpoint_proto) for endpoint_proto in proto.service_endpoint
            ),
        )
