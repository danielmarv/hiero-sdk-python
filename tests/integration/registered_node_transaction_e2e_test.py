"""Integration tests for the registered node lifecycle."""

from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateTransaction,
)
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)
from hiero_sdk_python.nodes.registered_node_update_transaction import (
    RegisteredNodeUpdateTransaction,
)
from hiero_sdk_python.response_code import ResponseCode


pytestmark = pytest.mark.integration


def test_registered_node_create_update_delete_live_network(env):
    """Create, update, and delete a registered node on a live network."""
    endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_api=BlockNodeApi.PUBLISH,
    )

    registered_node_id: int | None = None
    create_receipt = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_description("Python SDK live registered node test")
        .add_service_endpoint(endpoint)
        .execute(env.client)
    )

    if create_receipt.status == ResponseCode.UNAUTHORIZED:
        pytest.skip("Live network rejected registered-node create for this operator with UNAUTHORIZED.")

    assert create_receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status: {ResponseCode(create_receipt.status).name}"
    )
    registered_node_id = create_receipt.registered_node_id
    assert registered_node_id is not None

    try:
        update_receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_description("Python SDK live registered node updated")
            .add_service_endpoint(endpoint)
            .execute(env.client)
        )
        assert update_receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update failed with status: {ResponseCode(update_receipt.status).name}"
        )

    finally:
        if registered_node_id is not None:
            delete_receipt = (
                RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).execute(env.client)
            )
            assert delete_receipt.status == ResponseCode.SUCCESS, (
                f"Registered node delete failed with status: {ResponseCode(delete_receipt.status).name}"
            )


def test_registered_node_association_transaction_body_is_available():
    """Consensus-node association transaction support is available in the SDK body."""
    associate_transaction = NodeUpdateTransaction().set_node_id(3).add_associated_registered_node(1)

    assert associate_transaction is not None
