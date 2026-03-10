"""
RegisteredServiceEndpoint model for HIP-1137.

Represents a registered network node endpoint with address, port, TLS settings,
and endpoint type information (block node, mirror node, RPC relay, or general service).
"""

from enum import IntEnum
from typing import Optional

from hiero_sdk_python.hapi.services.basic_types_pb2 import ServiceEndpoint


class BlockNodeApi(IntEnum):
    """Well-known block node endpoint APIs."""
    OTHER = 0
    STATUS = 1
    PUBLISH = 2
    SUBSCRIBE_STREAM = 3
    STATE_PROOF = 4


class EndpointType(IntEnum):
    """Types of registered node endpoints."""
    BLOCK_NODE = 0
    MIRROR_NODE = 1
    RPC_RELAY = 2
    GENERAL_SERVICE = 3


class RegisteredServiceEndpoint:
    """
    Represents a registered network node service endpoint.

    Each registered network node publishes one or more endpoints to enable
    communication with clients. Supports IP address or FQDN, port, TLS
    requirement, and endpoint type classification.
    """

    def __init__(
        self,
        ip_address: Optional[bytes] = None,
        domain_name: Optional[str] = None,
        port: Optional[int] = None,
        requires_tls: bool = False,
        endpoint_type: Optional[EndpointType] = None,
        block_node_api: Optional[BlockNodeApi] = None,
        general_service_description: Optional[str] = None,
    ) -> None:
        self._ip_address: Optional[bytes] = ip_address
        self._domain_name: Optional[str] = domain_name
        self._port: Optional[int] = port
        self._requires_tls: bool = requires_tls
        self._endpoint_type: Optional[EndpointType] = endpoint_type
        self._block_node_api: Optional[BlockNodeApi] = block_node_api
        self._general_service_description: Optional[str] = general_service_description

    def set_ip_address(self, ip_address: bytes) -> "RegisteredServiceEndpoint":
        self._ip_address = ip_address
        self._domain_name = None
        return self

    def get_ip_address(self) -> Optional[bytes]:
        return self._ip_address

    def set_domain_name(self, domain_name: str) -> "RegisteredServiceEndpoint":
        self._domain_name = domain_name
        self._ip_address = None
        return self

    def get_domain_name(self) -> Optional[str]:
        return self._domain_name

    def set_port(self, port: int) -> "RegisteredServiceEndpoint":
        self._port = port
        return self

    def get_port(self) -> Optional[int]:
        return self._port

    def set_requires_tls(self, requires_tls: bool) -> "RegisteredServiceEndpoint":
        self._requires_tls = requires_tls
        return self

    def get_requires_tls(self) -> bool:
        return self._requires_tls

    def set_endpoint_type(self, endpoint_type: EndpointType) -> "RegisteredServiceEndpoint":
        self._endpoint_type = endpoint_type
        return self

    def get_endpoint_type(self) -> Optional[EndpointType]:
        return self._endpoint_type

    def set_block_node_api(self, block_node_api: BlockNodeApi) -> "RegisteredServiceEndpoint":
        self._block_node_api = block_node_api
        self._endpoint_type = EndpointType.BLOCK_NODE
        return self

    def get_block_node_api(self) -> Optional[BlockNodeApi]:
        return self._block_node_api

    def set_general_service_description(self, description: str) -> "RegisteredServiceEndpoint":
        self._general_service_description = description
        self._endpoint_type = EndpointType.GENERAL_SERVICE
        return self

    def get_general_service_description(self) -> Optional[str]:
        return self._general_service_description

    def _to_proto(self) -> ServiceEndpoint:
        """
        Converts this RegisteredServiceEndpoint to a protobuf ServiceEndpoint.

        Note: This uses the existing ServiceEndpoint proto as a wire format.
        When the HAPI protobuf definitions are updated to include the
        RegisteredServiceEndpoint message (per HIP-1137), this method should
        be updated to use the new proto type.
        """
        proto = ServiceEndpoint()
        if self._ip_address is not None:
            proto.ipAddressV4 = self._ip_address
        if self._domain_name is not None:
            proto.domain_name = self._domain_name
        if self._port is not None:
            proto.port = self._port
        return proto

    @classmethod
    def _from_proto(cls, service_endpoint: ServiceEndpoint) -> "RegisteredServiceEndpoint":
        """
        Creates a RegisteredServiceEndpoint from a protobuf ServiceEndpoint.

        Note: This uses the existing ServiceEndpoint proto as a wire format.
        When the HAPI protobuf definitions are updated to include the
        RegisteredServiceEndpoint message (per HIP-1137), this method should
        be updated to use the new proto type.
        """
        ip_address = service_endpoint.ipAddressV4 if service_endpoint.ipAddressV4 else None
        domain_name = service_endpoint.domain_name if service_endpoint.domain_name else None
        port = service_endpoint.port

        return cls(
            ip_address=ip_address,
            domain_name=domain_name,
            port=port,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RegisteredServiceEndpoint):
            return NotImplemented
        return (
            self._ip_address == other._ip_address
            and self._domain_name == other._domain_name
            and self._port == other._port
            and self._requires_tls == other._requires_tls
            and self._endpoint_type == other._endpoint_type
            and self._block_node_api == other._block_node_api
            and self._general_service_description == other._general_service_description
        )

    def __repr__(self) -> str:
        addr = self._domain_name or (self._ip_address.hex() if self._ip_address else "None")
        return (
            f"RegisteredServiceEndpoint(address={addr}, port={self._port}, "
            f"tls={self._requires_tls}, type={self._endpoint_type})"
        )
