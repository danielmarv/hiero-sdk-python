"""Unit tests for RegisteredNodeAddressBookQuery."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.general_service_endpoint import (
    GeneralServiceEndpoint,
)
from hiero_sdk_python.address_book.mirror_node_service_endpoint import (
    MirrorNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.registered_node_address_book_query import (
    RegisteredNodeAddressBookQuery,
)
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
    RpcRelayServiceEndpoint,
)
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import basic_types_pb2


pytestmark = pytest.mark.unit


@pytest.fixture
def client_mock():
    """Build a client mock with a mirror REST URL."""
    client = MagicMock()
    client.network.get_mirror_rest_url.return_value = "https://testnet.mirrornode.hedera.com/api/v1"
    return client


def test_execute_collects_pages_and_maps_models(client_mock):
    """Query should follow pagination and map mirror payloads to SDK models."""
    query = (
        RegisteredNodeAddressBookQuery()
        .set_limit(1)
        .set_order("desc")
        .set_type("mirror_node")
        .add_registered_node_id_filter("gte", 1)
    )

    admin_key_proto_hex = basic_types_pb2.Key(ed25519=b"\x11" * 32).SerializeToString().hex()

    page_one = {
        "registered_nodes": [
            {
                "registered_node_id": 7,
                "description": "Mirror endpoint",
                "admin_key": {
                    "_type": "ProtobufEncoded",
                    "key": admin_key_proto_hex,
                },
                "service_endpoints": [
                    {
                        "type": "MIRROR_NODE",
                        "domain_name": "mirror.example.com",
                        "port": 443,
                        "requires_tls": True,
                        "mirror_node": {},
                    }
                ],
            }
        ],
        "links": {"next": "/api/v1/network/registered-nodes?limit=1&registerednode.id=gt:7"},
    }
    page_two = {"registered_nodes": [], "links": {"next": None}}

    with patch(
        "hiero_sdk_python.address_book.registered_node_address_book_query.perform_query_to_mirror_node",
        side_effect=[page_one, page_two],
    ) as mock_query:
        address_book = query.execute(client_mock)

    assert len(address_book) == 1
    assert address_book[0].registered_node_id == 7
    assert address_book[0].description == "Mirror endpoint"
    assert address_book[0].admin_key is not None
    assert isinstance(address_book[0].service_endpoints[0], MirrorNodeServiceEndpoint)
    assert address_book[0].service_endpoints[0].domain_name == "mirror.example.com"
    assert address_book[0].service_endpoints[0].requires_tls is True

    assert mock_query.call_args_list == [
        call(
            "https://testnet.mirrornode.hedera.com/api/v1/network/registered-nodes"
            "?order=desc&limit=1&type=MIRROR_NODE&registerednode.id=gte%3A1",
            timeout=10.0,
        ),
        call(
            "https://testnet.mirrornode.hedera.com/api/v1/network/registered-nodes?limit=1&registerednode.id=gt:7",
            timeout=10.0,
        ),
    ]


def test_execute_uses_java_rest_port_for_local_registered_nodes_endpoint(client_mock):
    """Local registered-node mirror requests should use the Java REST API port."""
    client_mock.network.get_mirror_rest_url.return_value = "http://localhost:5551/api/v1"
    query = RegisteredNodeAddressBookQuery().set_limit(25).add_registered_node_id_filter("gte", 0)
    response = {"registered_nodes": [], "links": {"next": None}}

    with patch(
        "hiero_sdk_python.address_book.registered_node_address_book_query.perform_query_to_mirror_node",
        return_value=response,
    ) as mock_query:
        query.execute(client_mock)

    mock_query.assert_called_once_with(
        "http://localhost:8084/api/v1/network/registered-nodes?registerednode.id=gte%3A0",
        timeout=10.0,
    )


def test_execute_maps_block_node_endpoint_api(client_mock):
    """Block endpoint API values should map to BlockNodeApi members."""
    query = RegisteredNodeAddressBookQuery()
    response = {
        "registered_nodes": [
            {
                "registered_node_id": 8,
                "service_endpoints": [
                    {
                        "ip_address": "127.0.0.1",
                        "port": 50211,
                        "requires_tls": False,
                        "block_node": {"endpoint_apis": ["STATUS", "PUBLISH"]},
                    }
                ],
            }
        ],
        "links": {"next": None},
    }

    with patch(
        "hiero_sdk_python.address_book.registered_node_address_book_query.perform_query_to_mirror_node",
        return_value=response,
    ):
        address_book = query.execute(client_mock, timeout=3)

    endpoint = address_book[0].service_endpoints[0]
    assert isinstance(endpoint, BlockNodeServiceEndpoint)
    assert endpoint.endpoint_api is BlockNodeApi.STATUS
    assert endpoint.endpoint_apis == [BlockNodeApi.STATUS, BlockNodeApi.PUBLISH]


def test_execute_maps_rpc_relay_and_general_service_endpoints(client_mock):
    """Mirror payloads should map RPC relay and general service endpoints."""
    query = RegisteredNodeAddressBookQuery()
    response = {
        "registered_nodes": [
            {
                "registered_node_id": 9,
                "service_endpoints": [
                    {
                        "domain_name": "relay.example.com",
                        "port": 7545,
                        "type": "RPC_RELAY",
                        "rpc_relay": {},
                    },
                    {
                        "domain_name": "general.example.com",
                        "port": 443,
                        "type": "GENERAL_SERVICE",
                        "general_service": {"description": "general service"},
                    },
                ],
            }
        ],
        "links": {"next": None},
    }

    with patch(
        "hiero_sdk_python.address_book.registered_node_address_book_query.perform_query_to_mirror_node",
        return_value=response,
    ):
        address_book = query.execute(client_mock)

    relay_endpoint = address_book[0].service_endpoints[0]
    general_endpoint = address_book[0].service_endpoints[1]
    assert isinstance(relay_endpoint, RpcRelayServiceEndpoint)
    assert isinstance(general_endpoint, GeneralServiceEndpoint)
    assert general_endpoint.description == "general service"


def test_execute_maps_protobuf_encoded_key_list_admin_key(client_mock):
    """ProtobufEncoded mirror admin keys should preserve complex Key values."""
    query = RegisteredNodeAddressBookQuery()
    first_key = PrivateKey.generate_ed25519().public_key()
    second_key = PrivateKey.generate_ed25519().public_key()
    admin_key_hex = KeyList([first_key, second_key], threshold=1).to_proto_key().SerializeToString().hex()
    response = {
        "registered_nodes": [
            {
                "registered_node_id": 9,
                "admin_key": {"_type": "ProtobufEncoded", "key": admin_key_hex},
                "service_endpoints": [
                    {
                        "domain_name": "mirror.example.com",
                        "port": 443,
                        "mirror_node": {},
                    }
                ],
            }
        ],
        "links": {"next": None},
    }

    with patch(
        "hiero_sdk_python.address_book.registered_node_address_book_query.perform_query_to_mirror_node",
        return_value=response,
    ):
        address_book = query.execute(client_mock)

    assert isinstance(address_book[0].admin_key, KeyList)
    assert len(address_book[0].admin_key.keys) == 2
    assert address_book[0].admin_key.threshold == 1


def test_execute_rejects_invalid_registered_nodes_payload(client_mock):
    """Query should reject payloads that violate expected mirror response shape."""
    query = RegisteredNodeAddressBookQuery()
    invalid_response = {"registered_nodes": "invalid", "links": {"next": None}}

    with (
        patch(
            "hiero_sdk_python.address_book.registered_node_address_book_query.perform_query_to_mirror_node",
            return_value=invalid_response,
        ),
        pytest.raises(ValueError, match="registered_nodes"),
    ):
        query.execute(client_mock)


def test_query_validates_filter_inputs():
    """Builder methods should reject invalid filter input values."""
    query = RegisteredNodeAddressBookQuery()

    with pytest.raises(ValueError, match="limit"):
        query.set_limit(0)

    with pytest.raises(ValueError, match="order"):
        query.set_order("sideways")

    with pytest.raises(ValueError, match="type"):
        query.set_type("something_else")

    with pytest.raises(ValueError, match="operator"):
        query.add_registered_node_id_filter("between", 1)

    with pytest.raises(ValueError, match="non-negative"):
        query.set_registered_node_id(-1)

    query.set_registered_node_id(1)
    with pytest.raises(ValueError, match="eq filter"):
        query.add_registered_node_id_filter("gt", 2)
