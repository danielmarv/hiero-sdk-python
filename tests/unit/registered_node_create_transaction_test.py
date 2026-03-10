"""
Test cases for the RegisteredNodeCreateTransaction class (HIP-1137).
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
    EndpointType,
    BlockNodeApi,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateParams,
    RegisteredNodeCreateTransaction,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def admin_key():
    return PrivateKey.generate_ed25519().public_key()


@pytest.fixture
def service_endpoints():
    return [
        RegisteredServiceEndpoint(
            domain_name="block.example.com",
            port=8080,
            requires_tls=True,
            endpoint_type=EndpointType.BLOCK_NODE,
            block_node_api=BlockNodeApi.STATUS,
        ),
    ]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    tx = RegisteredNodeCreateTransaction()

    assert tx.admin_key is None
    assert tx.description is None
    assert tx.service_endpoints == []
    assert tx.node_account is None


def test_constructor_with_params(admin_key, service_endpoints):
    """Test creating with constructor parameters."""
    params = RegisteredNodeCreateParams(
        admin_key=admin_key,
        description="Test block node",
        service_endpoints=service_endpoints,
        node_account=AccountId(0, 0, 100),
    )

    tx = RegisteredNodeCreateTransaction(params=params)

    assert tx.admin_key == admin_key
    assert tx.description == "Test block node"
    assert tx.service_endpoints == service_endpoints
    assert tx.node_account == AccountId(0, 0, 100)


def test_set_admin_key(admin_key):
    """Test setting admin_key via setter."""
    tx = RegisteredNodeCreateTransaction()
    result = tx.set_admin_key(admin_key)

    assert tx.admin_key == admin_key
    assert result is tx


def test_set_description():
    """Test setting description via setter."""
    tx = RegisteredNodeCreateTransaction()
    result = tx.set_description("My block node")

    assert tx.description == "My block node"
    assert result is tx


def test_set_service_endpoints(service_endpoints):
    """Test setting service_endpoints via setter."""
    tx = RegisteredNodeCreateTransaction()
    result = tx.set_service_endpoints(service_endpoints)

    assert tx.service_endpoints == service_endpoints
    assert result is tx


def test_set_node_account():
    """Test setting node_account via setter."""
    tx = RegisteredNodeCreateTransaction()
    account = AccountId(0, 0, 200)
    result = tx.set_node_account(account)

    assert tx.node_account == account
    assert result is tx


def test_build_proto_body_missing_admin_key(service_endpoints):
    """Test that building without admin_key raises ValueError."""
    tx = RegisteredNodeCreateTransaction()
    tx.service_endpoints = service_endpoints

    with pytest.raises(ValueError, match="admin_key"):
        tx._build_proto_body()


def test_build_proto_body_empty_endpoints(admin_key):
    """Test that building with empty endpoints raises ValueError."""
    tx = RegisteredNodeCreateTransaction()
    tx.admin_key = admin_key

    with pytest.raises(ValueError, match="service_endpoints"):
        tx._build_proto_body()


def test_build_proto_body_too_many_endpoints(admin_key):
    """Test that building with >50 endpoints raises ValueError."""
    tx = RegisteredNodeCreateTransaction()
    tx.admin_key = admin_key
    tx.service_endpoints = [
        RegisteredServiceEndpoint(domain_name=f"node{i}.example.com", port=8080)
        for i in range(51)
    ]

    with pytest.raises(ValueError, match="50"):
        tx._build_proto_body()


def test_build_proto_body_valid(admin_key, service_endpoints):
    """Test building a valid proto body."""
    tx = RegisteredNodeCreateTransaction()
    tx.admin_key = admin_key
    tx.description = "Test node"
    tx.service_endpoints = service_endpoints
    tx.node_account = AccountId(0, 0, 100)

    body = tx._build_proto_body()

    assert body.admin_key == admin_key._to_proto()
    assert body.description == "Test node"
    assert len(body.service_endpoint) == 1
    assert body.node_account == AccountId(0, 0, 100)._to_proto()


def test_setter_requires_not_frozen(admin_key, service_endpoints):
    """Test that setters raise an error when transaction is frozen."""
    tx = RegisteredNodeCreateTransaction()
    tx.admin_key = admin_key
    tx.service_endpoints = service_endpoints
    # Simulate frozen state
    tx._transaction_body_bytes[AccountId(0, 0, 3)] = b"frozen"

    with pytest.raises(Exception):
        tx.set_admin_key(admin_key)

    with pytest.raises(Exception):
        tx.set_description("frozen")

    with pytest.raises(Exception):
        tx.set_service_endpoints([])

    with pytest.raises(Exception):
        tx.set_node_account(AccountId(0, 0, 1))
