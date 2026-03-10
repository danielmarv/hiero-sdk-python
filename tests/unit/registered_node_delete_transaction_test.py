"""
Test cases for the RegisteredNodeDeleteTransaction class (HIP-1137).
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)

pytestmark = pytest.mark.unit


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    tx = RegisteredNodeDeleteTransaction()
    assert tx.registered_node_id is None


def test_constructor_with_node_id():
    """Test creating with a registered_node_id."""
    tx = RegisteredNodeDeleteTransaction(registered_node_id=42)
    assert tx.registered_node_id == 42


def test_set_registered_node_id():
    """Test setting registered_node_id via setter."""
    tx = RegisteredNodeDeleteTransaction()
    result = tx.set_registered_node_id(42)

    assert tx.registered_node_id == 42
    assert result is tx


def test_build_proto_body_missing_node_id():
    """Test that building without registered_node_id raises ValueError."""
    tx = RegisteredNodeDeleteTransaction()

    with pytest.raises(ValueError, match="registered_node_id"):
        tx._build_proto_body()


def test_build_proto_body_valid():
    """Test building a valid proto body."""
    tx = RegisteredNodeDeleteTransaction(registered_node_id=42)

    body = tx._build_proto_body()

    assert body.registered_node_id == 42


def test_setter_requires_not_frozen():
    """Test that setter raises an error when transaction is frozen."""
    tx = RegisteredNodeDeleteTransaction(registered_node_id=42)
    # Simulate frozen state
    tx._transaction_body_bytes[AccountId(0, 0, 3)] = b"frozen"

    with pytest.raises(Exception):
        tx.set_registered_node_id(99)
