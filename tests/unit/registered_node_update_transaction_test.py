"""
Test cases for the RegisteredNodeUpdateTransaction class (HIP-1137).
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
    EndpointType,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_update_transaction import (
    RegisteredNodeUpdateParams,
    RegisteredNodeUpdateTransaction,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def admin_key():
    return PrivateKey.generate_ed25519().public_key()


@pytest.fixture
def service_endpoints():
    return [
        RegisteredServiceEndpoint(
            domain_name="mirror.example.com",
            port=443,
            requires_tls=True,
            endpoint_type=EndpointType.MIRROR_NODE,
        ),
    ]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    tx = RegisteredNodeUpdateTransaction()

    assert tx.registered_node_id is None
    assert tx.admin_key is None
    assert tx.description is None
    assert tx.service_endpoints == []
    assert tx.node_account is None


def test_constructor_with_params(admin_key, service_endpoints):
    """Test creating with constructor parameters."""
    params = RegisteredNodeUpdateParams(
        registered_node_id=42,
        admin_key=admin_key,
        description="Updated node",
        service_endpoints=service_endpoints,
        node_account=AccountId(0, 0, 100),
    )

    tx = RegisteredNodeUpdateTransaction(params=params)

    assert tx.registered_node_id == 42
    assert tx.admin_key == admin_key
    assert tx.description == "Updated node"
    assert tx.service_endpoints == service_endpoints
    assert tx.node_account == AccountId(0, 0, 100)


def test_set_registered_node_id():
    """Test setting registered_node_id via setter."""
    tx = RegisteredNodeUpdateTransaction()
    result = tx.set_registered_node_id(42)

    assert tx.registered_node_id == 42
    assert result is tx


def test_set_admin_key(admin_key):
    """Test setting admin_key via setter."""
    tx = RegisteredNodeUpdateTransaction()
    result = tx.set_admin_key(admin_key)

    assert tx.admin_key == admin_key
    assert result is tx


def test_set_description():
    """Test setting description via setter."""
    tx = RegisteredNodeUpdateTransaction()
    result = tx.set_description("Updated description")

    assert tx.description == "Updated description"
    assert result is tx


def test_set_service_endpoints(service_endpoints):
    """Test setting service_endpoints via setter."""
    tx = RegisteredNodeUpdateTransaction()
    result = tx.set_service_endpoints(service_endpoints)

    assert tx.service_endpoints == service_endpoints
    assert result is tx


def test_set_node_account():
    """Test setting node_account via setter."""
    tx = RegisteredNodeUpdateTransaction()
    account = AccountId(0, 0, 200)
    result = tx.set_node_account(account)

    assert tx.node_account == account
    assert result is tx


def test_build_proto_body_missing_node_id():
    """Test that building without registered_node_id raises ValueError."""
    tx = RegisteredNodeUpdateTransaction()

    with pytest.raises(ValueError, match="registered_node_id"):
        tx._build_proto_body()


def test_build_proto_body_too_many_endpoints():
    """Test that building with >50 endpoints raises ValueError."""
    tx = RegisteredNodeUpdateTransaction()
    tx.registered_node_id = 42
    tx.service_endpoints = [
        RegisteredServiceEndpoint(domain_name=f"node{i}.example.com", port=8080)
        for i in range(51)
    ]

    with pytest.raises(ValueError, match="50"):
        tx._build_proto_body()


def test_build_proto_body_valid(admin_key, service_endpoints):
    """Test building a valid proto body."""
    tx = RegisteredNodeUpdateTransaction()
    tx.registered_node_id = 42
    tx.admin_key = admin_key
    tx.description = "Updated node"
    tx.service_endpoints = service_endpoints
    tx.node_account = AccountId(0, 0, 100)

    body = tx._build_proto_body()

    assert body.registered_node_id == 42
    assert body.admin_key == admin_key._to_proto()
    assert body.description.value == "Updated node"
    assert len(body.service_endpoint) == 1
    assert body.node_account == AccountId(0, 0, 100)._to_proto()


def test_build_proto_body_minimal():
    """Test building with just required fields."""
    tx = RegisteredNodeUpdateTransaction()
    tx.registered_node_id = 1

    body = tx._build_proto_body()

    assert body.registered_node_id == 1


def test_setter_requires_not_frozen(admin_key):
    """Test that setters raise an error when transaction is frozen."""
    tx = RegisteredNodeUpdateTransaction()
    tx.registered_node_id = 42
    # Simulate frozen state
    tx._transaction_body_bytes[AccountId(0, 0, 3)] = b"frozen"

    with pytest.raises(Exception):
        tx.set_registered_node_id(99)

    with pytest.raises(Exception):
        tx.set_admin_key(admin_key)

    with pytest.raises(Exception):
        tx.set_description("frozen")

    with pytest.raises(Exception):
        tx.set_service_endpoints([])

    with pytest.raises(Exception):
        tx.set_node_account(AccountId(0, 0, 1))
