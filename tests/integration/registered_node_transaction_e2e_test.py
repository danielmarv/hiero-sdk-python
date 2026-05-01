"""Integration tests for registered node transactions."""

from __future__ import annotations

import grpc
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
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
    RpcRelayServiceEndpoint,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError, ReceiptStatusError
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


def _skip_if_registered_node_api_unavailable(error: Exception) -> None:
    """Skip when the network stack does not expose registered-node RPC methods."""
    if isinstance(error, grpc.RpcError) and error.code() == grpc.StatusCode.UNIMPLEMENTED:
        pytest.skip("Registered-node RPC methods are unavailable on this network stack.")

    error_text = str(error)

    if "Method not found: proto.AddressBookService/" in error_text:
        pytest.skip("Registered-node RPC methods are unavailable on this network stack.")

    if (
        isinstance(error, MaxAttemptsError)
        and "StatusCode.UNAVAILABLE" in error_text
        and ("Connection refused" in error_text or "Socket closed" in error_text)
    ):
        pytest.skip("Local Solo gRPC endpoint is unavailable on localhost:50211.")


def _execute_registered_node_transaction(transaction, env, **kwargs):
    """Execute a registered-node transaction and skip if RPC method is unavailable."""
    try:
        return transaction.execute(env.client, **kwargs)
    except Exception as error:
        _skip_if_registered_node_api_unavailable(error)
        raise


def _block_node_endpoint(domain_name: str = "blocks.example.com") -> BlockNodeServiceEndpoint:
    return BlockNodeServiceEndpoint(
        domain_name=domain_name,
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.STATUS],
    )


def _create_registered_node(
    env,
    admin_key: PrivateKey,
    service_endpoints: list[RegisteredServiceEndpoint] | None = None,
    description: str = "Python SDK registered node",
) -> int:
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key.public_key())
        .set_description(description)
        .set_service_endpoints(service_endpoints or [_block_node_endpoint()])
        .freeze_with(env.client)
        .sign(admin_key)
    )
    receipt = _execute_registered_node_transaction(transaction, env)

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status: {ResponseCode(receipt.status).name}"
    )
    assert receipt.registered_node_id is not None
    return receipt.registered_node_id


def _delete_registered_node(env, registered_node_id: int, admin_key: PrivateKey) -> None:
    transaction = (
        RegisteredNodeDeleteTransaction()
        .set_registered_node_id(registered_node_id)
        .freeze_with(env.client)
        .sign(admin_key)
    )
    receipt = _execute_registered_node_transaction(transaction, env)

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node delete failed with status: {ResponseCode(receipt.status).name}"
    )


def test_registered_node_create_with_block_node_endpoint(env):
    """Create a registered node with a block-node endpoint."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(env, admin_key)

    _delete_registered_node(env, registered_node_id, admin_key)


def test_registered_node_create_with_multiple_service_endpoints(env):
    """Create a registered node with every supported service endpoint type."""
    admin_key = PrivateKey.generate_ed25519()
    service_endpoints: list[RegisteredServiceEndpoint] = [
        _block_node_endpoint("test.block.com"),
        MirrorNodeServiceEndpoint(ip_address=bytes([127, 0, 0, 1]), port=443),
        RpcRelayServiceEndpoint(domain_name="test.rpc.com", port=443),
        GeneralServiceEndpoint(domain_name="test.general.com", port=8080),
    ]
    registered_node_id = _create_registered_node(env, admin_key, service_endpoints)

    _delete_registered_node(env, registered_node_id, admin_key)


def test_registered_node_update_endpoints_and_description(env):
    """Update a registered node's service endpoints and description."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(
        env,
        admin_key,
        service_endpoints=[_block_node_endpoint("initial.blocks.com")],
        description="Python SDK initial registered node",
    )

    try:
        transaction = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_description("Python SDK updated registered node")
            .set_service_endpoints([_block_node_endpoint("updated.blocks.com")])
            .freeze_with(env.client)
            .sign(admin_key)
        )
        receipt = _execute_registered_node_transaction(transaction, env)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update failed with status: {ResponseCode(receipt.status).name}"
        )
    finally:
        _delete_registered_node(env, registered_node_id, admin_key)


def test_registered_node_update_can_rotate_admin_key(env):
    """Rotate a registered node admin key by signing with the old and new keys."""
    old_admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(env, old_admin_key)
    new_admin_key = PrivateKey.generate_ed25519()
    current_admin_key = old_admin_key

    try:
        transaction = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_admin_key(new_admin_key.public_key())
            .freeze_with(env.client)
            .sign(old_admin_key)
            .sign(new_admin_key)
        )
        receipt = _execute_registered_node_transaction(transaction, env)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node admin key rotation failed with status: {ResponseCode(receipt.status).name}"
        )
        current_admin_key = new_admin_key
    finally:
        _delete_registered_node(env, registered_node_id, current_admin_key)


def test_registered_node_delete(env):
    """Delete a registered node."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(env, admin_key)

    _delete_registered_node(env, registered_node_id, admin_key)


def test_registered_node_delete_fails_when_still_associated(env):
    """Deleting an associated registered node should fail with REGISTERED_NODE_STILL_ASSOCIATED."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(env, admin_key)
    associated = False

    try:
        associate_receipt = (
            NodeUpdateTransaction()
            .set_node_id(0)
            .add_associated_registered_node(registered_node_id)
            .execute(env.client)
        )
        assert associate_receipt.status == ResponseCode.SUCCESS, (
            f"Registered node association failed with status: {ResponseCode(associate_receipt.status).name}"
        )
        associated = True

        delete_transaction = (
            RegisteredNodeDeleteTransaction()
            .set_registered_node_id(registered_node_id)
            .freeze_with(env.client)
            .sign(admin_key)
        )
        delete_response = _execute_registered_node_transaction(delete_transaction, env, wait_for_receipt=False)

        with pytest.raises(ReceiptStatusError) as error:
            delete_response.get_receipt(env.client, validate_status=True)

        assert error.value.status == ResponseCode.REGISTERED_NODE_STILL_ASSOCIATED
    finally:
        if associated:
            clear_receipt = (
                NodeUpdateTransaction().set_node_id(0).clear_associated_registered_nodes().execute(env.client)
            )
            assert clear_receipt.status == ResponseCode.SUCCESS, (
                f"Registered node association cleanup failed with status: {ResponseCode(clear_receipt.status).name}"
            )

        _delete_registered_node(env, registered_node_id, admin_key)


def test_registered_node_association_transaction_body_is_available():
    """Consensus-node association transaction support is available in the SDK body."""
    associate_transaction = NodeUpdateTransaction().set_node_id(3).add_associated_registered_node(1)

    assert associate_transaction is not None
