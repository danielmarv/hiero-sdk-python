"""Live integration tests for RegisteredNodeAddressBookQuery against mirror REST APIs."""

from __future__ import annotations

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
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateTransaction,
)
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils import wait_for_mirror_node


pytestmark = pytest.mark.integration


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

    create_receipt = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key.public_key())
        .set_description(description)
        .set_service_endpoints(service_endpoints)
        .freeze_with(env.client)
        .sign(admin_key)
        .execute(env.client)
    )

    assert create_receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status: {ResponseCode(create_receipt.status).name}"
    )
    assert create_receipt.registered_node_id is not None
    registered_node_id = create_receipt.registered_node_id

    try:
        address_book = wait_for_mirror_node(
            lambda: RegisteredNodeAddressBookQuery().set_registered_node_id(registered_node_id).execute(env.client),
            lambda result: len(result) == 1,
            timeout=15,
            interval=1,
        )

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
