"""Registered block node service endpoint."""

from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


@dataclass(eq=True, init=False)
class BlockNodeServiceEndpoint(RegisteredServiceEndpoint):
    """A registered endpoint for a block node service."""

    endpoint_apis: list[BlockNodeApi] = field(default_factory=lambda: [BlockNodeApi.OTHER])

    def __init__(
        self,
        ip_address: bytes | None = None,
        domain_name: str | None = None,
        port: int = 0,
        requires_tls: bool = False,
        endpoint_apis: list[BlockNodeApi] | None = None,
        endpoint_api: BlockNodeApi | None = None,
    ) -> None:
        """Initialize a block-node endpoint.

        ``endpoint_api`` is retained as a compatibility alias for callers that
        only need a single API value.
        """
        if endpoint_apis is not None and endpoint_api is not None:
            raise ValueError("Only one of endpoint_apis or endpoint_api may be set.")

        apis = endpoint_apis
        if apis is None:
            apis = [endpoint_api if endpoint_api is not None else BlockNodeApi.OTHER]
        if not apis:
            raise ValueError("endpoint_apis must contain at least one BlockNodeApi.")

        self.ip_address = ip_address
        self.domain_name = domain_name
        self.port = port
        self.requires_tls = requires_tls
        self.endpoint_apis = [BlockNodeApi(api) for api in apis]
        RegisteredServiceEndpoint.__post_init__(self)

    @property
    def endpoint_api(self) -> BlockNodeApi:
        """Return the first endpoint API for compatibility with older callers."""
        return self.endpoint_apis[0]

    @endpoint_api.setter
    def endpoint_api(self, endpoint_api: BlockNodeApi) -> None:
        """Replace endpoint APIs with a single compatibility value."""
        self.endpoint_apis = [BlockNodeApi(endpoint_api)]

    def _endpoint_type_proto(self) -> dict[str, RegisteredServiceEndpointProto.BlockNodeEndpoint]:
        """Return the protobuf block-node subtype."""
        return {
            "block_node": RegisteredServiceEndpointProto.BlockNodeEndpoint(
                endpoint_api=[int(api) for api in self.endpoint_apis]
            )
        }

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> BlockNodeServiceEndpoint:
        """Build a block node endpoint from protobuf."""
        endpoint_apis = [BlockNodeApi(endpoint_api) for endpoint_api in proto.block_node.endpoint_api] or [
            BlockNodeApi.OTHER
        ]
        return cls(
            endpoint_apis=endpoint_apis,
            **cls._base_kwargs_from_proto(proto),
        )
