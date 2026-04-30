"""Unit tests for the RegisteredNode model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.registered_node import RegisteredNode
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.state.addressbook.registered_node_pb2 import (
    RegisteredNode as RegisteredNodeProto,
)


pytestmark = pytest.mark.unit


def test_registered_node_roundtrip():
    """Registered nodes should round-trip through protobuf."""
    admin_key = PrivateKey.generate_ed25519().public_key()
    endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_api=BlockNodeApi.STATUS,
    )
    node = RegisteredNode(
        registered_node_id=12,
        admin_key=admin_key,
        description="mirrorable block node",
        service_endpoints=(endpoint,),
    )

    proto = node._to_proto()
    roundtrip = RegisteredNode._from_proto(proto)

    assert isinstance(proto, RegisteredNodeProto)
    assert roundtrip == node


def test_registered_node_is_immutable():
    """Registered nodes should be immutable once constructed."""
    node = RegisteredNode(registered_node_id=12)

    with pytest.raises(FrozenInstanceError):
        node.registered_node_id = 13


def test_registered_node_roundtrips_key_list_admin_key():
    """Registered nodes should preserve complex admin keys."""
    first_key = PrivateKey.generate_ed25519().public_key()
    second_key = PrivateKey.generate_ed25519().public_key()
    node = RegisteredNode(
        registered_node_id=12,
        admin_key=KeyList([first_key, second_key], threshold=1),
    )

    roundtrip = RegisteredNode._from_proto(node._to_proto())

    assert isinstance(roundtrip.admin_key, KeyList)
    assert len(roundtrip.admin_key.keys) == 2
    assert roundtrip.admin_key.threshold == 1


def test_registered_node_rejects_description_over_100_bytes():
    """Registered node descriptions are capped at 100 UTF-8 bytes."""
    with pytest.raises(ValueError, match="description must not exceed 100 UTF-8 bytes"):
        RegisteredNode(registered_node_id=12, description="x" * 101)
