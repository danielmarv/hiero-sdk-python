"""
Test cases for the RegisteredServiceEndpoint model (HIP-1137).
"""

import pytest

from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
    EndpointType,
    BlockNodeApi,
)

pytestmark = pytest.mark.unit


def test_constructor_defaults():
    """Test default values."""
    endpoint = RegisteredServiceEndpoint()

    assert endpoint.get_ip_address() is None
    assert endpoint.get_domain_name() is None
    assert endpoint.get_port() is None
    assert endpoint.get_requires_tls() is False
    assert endpoint.get_endpoint_type() is None
    assert endpoint.get_block_node_api() is None
    assert endpoint.get_general_service_description() is None


def test_constructor_with_params():
    """Test construction with parameters."""
    endpoint = RegisteredServiceEndpoint(
        domain_name="block.example.com",
        port=8080,
        requires_tls=True,
        endpoint_type=EndpointType.BLOCK_NODE,
        block_node_api=BlockNodeApi.STATUS,
    )

    assert endpoint.get_domain_name() == "block.example.com"
    assert endpoint.get_port() == 8080
    assert endpoint.get_requires_tls() is True
    assert endpoint.get_endpoint_type() == EndpointType.BLOCK_NODE
    assert endpoint.get_block_node_api() == BlockNodeApi.STATUS


def test_set_ip_address_clears_domain():
    """Test that setting IP address clears domain name."""
    endpoint = RegisteredServiceEndpoint(domain_name="example.com")
    endpoint.set_ip_address(b'\x7f\x00\x00\x01')

    assert endpoint.get_ip_address() == b'\x7f\x00\x00\x01'
    assert endpoint.get_domain_name() is None


def test_set_domain_name_clears_ip():
    """Test that setting domain name clears IP address."""
    endpoint = RegisteredServiceEndpoint(ip_address=b'\x7f\x00\x00\x01')
    endpoint.set_domain_name("example.com")

    assert endpoint.get_domain_name() == "example.com"
    assert endpoint.get_ip_address() is None


def test_builder_pattern():
    """Test method chaining (builder pattern)."""
    endpoint = (
        RegisteredServiceEndpoint()
        .set_domain_name("relay.example.com")
        .set_port(443)
        .set_requires_tls(True)
        .set_endpoint_type(EndpointType.RPC_RELAY)
    )

    assert endpoint.get_domain_name() == "relay.example.com"
    assert endpoint.get_port() == 443
    assert endpoint.get_requires_tls() is True
    assert endpoint.get_endpoint_type() == EndpointType.RPC_RELAY


def test_set_block_node_api_sets_type():
    """Test that set_block_node_api also sets endpoint type."""
    endpoint = RegisteredServiceEndpoint()
    endpoint.set_block_node_api(BlockNodeApi.PUBLISH)

    assert endpoint.get_endpoint_type() == EndpointType.BLOCK_NODE
    assert endpoint.get_block_node_api() == BlockNodeApi.PUBLISH


def test_set_general_service_description_sets_type():
    """Test that set_general_service_description also sets endpoint type."""
    endpoint = RegisteredServiceEndpoint()
    endpoint.set_general_service_description("Custom indexer")

    assert endpoint.get_endpoint_type() == EndpointType.GENERAL_SERVICE
    assert endpoint.get_general_service_description() == "Custom indexer"


def test_equality():
    """Test equality comparison."""
    e1 = RegisteredServiceEndpoint(
        domain_name="example.com",
        port=8080,
        requires_tls=True,
        endpoint_type=EndpointType.MIRROR_NODE,
    )
    e2 = RegisteredServiceEndpoint(
        domain_name="example.com",
        port=8080,
        requires_tls=True,
        endpoint_type=EndpointType.MIRROR_NODE,
    )
    e3 = RegisteredServiceEndpoint(
        domain_name="other.com",
        port=8080,
    )

    assert e1 == e2
    assert e1 != e3


def test_to_proto_domain_name():
    """Test proto conversion with domain name."""
    endpoint = RegisteredServiceEndpoint(
        domain_name="block.example.com",
        port=8080,
    )

    proto = endpoint._to_proto()

    assert proto.domain_name == "block.example.com"
    assert proto.port == 8080


def test_to_proto_ip_address():
    """Test proto conversion with IP address."""
    endpoint = RegisteredServiceEndpoint(
        ip_address=b'\x0a\x00\x00\x01',
        port=50211,
    )

    proto = endpoint._to_proto()

    assert proto.ipAddressV4 == b'\x0a\x00\x00\x01'
    assert proto.port == 50211


def test_from_proto_roundtrip():
    """Test from_proto creates proper instance."""
    original = RegisteredServiceEndpoint(
        domain_name="mirror.example.com",
        port=443,
    )

    proto = original._to_proto()
    restored = RegisteredServiceEndpoint._from_proto(proto)

    assert restored.get_domain_name() == "mirror.example.com"
    assert restored.get_port() == 443


def test_repr():
    """Test string representation."""
    endpoint = RegisteredServiceEndpoint(
        domain_name="test.com",
        port=8080,
        endpoint_type=EndpointType.BLOCK_NODE,
    )

    repr_str = repr(endpoint)
    assert "test.com" in repr_str
    assert "8080" in repr_str


def test_block_node_api_enum():
    """Test BlockNodeApi enum values."""
    assert BlockNodeApi.OTHER == 0
    assert BlockNodeApi.STATUS == 1
    assert BlockNodeApi.PUBLISH == 2
    assert BlockNodeApi.SUBSCRIBE_STREAM == 3
    assert BlockNodeApi.STATE_PROOF == 4


def test_endpoint_type_enum():
    """Test EndpointType enum values."""
    assert EndpointType.BLOCK_NODE == 0
    assert EndpointType.MIRROR_NODE == 1
    assert EndpointType.RPC_RELAY == 2
    assert EndpointType.GENERAL_SERVICE == 3
