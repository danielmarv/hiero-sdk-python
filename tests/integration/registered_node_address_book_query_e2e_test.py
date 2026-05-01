"""Live integration tests for RegisteredNodeAddressBookQuery against mirror REST APIs."""

from __future__ import annotations

import grpc
import pytest

from hiero_sdk_python import RegisteredNodeAddressBookQuery
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
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
    RpcRelayServiceEndpoint,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateTransaction,
)
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils import wait_for_mirror_node


pytestmark = pytest.mark.integration


def _skip_if_registered_node_api_unavailable(error: Exception) -> None:
    """Skip when the network stack does not expose registered-node APIs."""
    if isinstance(error, grpc.RpcError) and error.code() == grpc.StatusCode.UNIMPLEMENTED:
        pytest.skip("Registered-node RPC methods are unavailable on this network stack.")

    details = str(error)
    if "Method not found: proto.AddressBookService/" in details:
        pytest.skip("Registered-node RPC methods are unavailable on this network stack.")
    if (
        isinstance(error, MaxAttemptsError)
        and "StatusCode.UNAVAILABLE" in details
        and ("Connection refused" in details or "Socket closed" in details)
    ):
        pytest.skip("Local Solo gRPC endpoint is unavailable on localhost:50211.")
    if "registered-nodes" in details and "404" in details:
        pytest.skip("Mirror node does not expose the registered-nodes endpoint on this network stack.")


def test_integration_registered_node_address_book_query_finds_created_node(env):
    """Create a registered node and verify it through the mirror registered-nodes endpoint."""
    admin_key = PrivateKey.generate_ed25519()
    description = "Python SDK registered node mirror query"
    service_endpoints = [
        BlockNodeServiceEndpoint(
            domain_name="test.block.com",
            port=443,
            requires_tls=True,
            endpoint_apis=[BlockNodeApi.STATUS],
        ),
        MirrorNodeServiceEndpoint(ip_address=bytes([127, 0, 0, 1]), port=443),
        RpcRelayServiceEndpoint(domain_name="test.rpc.com", port=443),
        GeneralServiceEndpoint(domain_name="test.general.com", port=8080),
    ]

    try:
        create_receipt = (
            RegisteredNodeCreateTransaction()
            .set_admin_key(admin_key.public_key())
            .set_description(description)
            .set_service_endpoints(service_endpoints)
            .freeze_with(env.client)
            .sign(admin_key)
            .execute(env.client)
        )
    except Exception as error:
        _skip_if_registered_node_api_unavailable(error)
        raise

    assert create_receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status: {ResponseCode(create_receipt.status).name}"
    )
    assert create_receipt.registered_node_id is not None
    registered_node_id = create_receipt.registered_node_id

    try:
        try:
            address_book = wait_for_mirror_node(
                lambda: RegisteredNodeAddressBookQuery().set_registered_node_id(registered_node_id).execute(env.client),
                lambda result: len(result) == 1,
                timeout=15,
                interval=1,
            )
        except Exception as error:
            _skip_if_registered_node_api_unavailable(error)
            raise

        assert len(address_book) == 1
        registered_node = address_book[0]
        assert registered_node.registered_node_id == registered_node_id
        assert registered_node.description == description
        assert len(registered_node.service_endpoints) == 4
        assert any(isinstance(endpoint, BlockNodeServiceEndpoint) for endpoint in registered_node.service_endpoints)
        assert any(isinstance(endpoint, MirrorNodeServiceEndpoint) for endpoint in registered_node.service_endpoints)
        assert any(isinstance(endpoint, RpcRelayServiceEndpoint) for endpoint in registered_node.service_endpoints)
        assert any(isinstance(endpoint, GeneralServiceEndpoint) for endpoint in registered_node.service_endpoints)
    finally:
        try:
            delete_receipt = (
                RegisteredNodeDeleteTransaction()
                .set_registered_node_id(registered_node_id)
                .freeze_with(env.client)
                .sign(admin_key)
                .execute(env.client)
            )
            assert delete_receipt.status == ResponseCode.SUCCESS, (
                f"Registered node delete failed with status: {ResponseCode(delete_receipt.status).name}"
            )
        except Exception as error:
            _skip_if_registered_node_api_unavailable(error)
            raise
