"""Live integration tests for RegisteredNodeAddressBookQuery against mirror REST APIs."""

from __future__ import annotations

import pytest

from hiero_sdk_python import RegisteredNodeAddressBookQuery
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.mirror_node_service_endpoint import (
    MirrorNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
    RpcRelayServiceEndpoint,
)


pytestmark = pytest.mark.integration


def test_integration_registered_node_address_book_query_live_mirror(env):
    """Query should execute successfully against the live mirror registered-nodes endpoint."""
    query = RegisteredNodeAddressBookQuery().set_limit(25).set_order("asc").add_registered_node_id_filter("gte", 0)

    address_book = query.execute(env.client, timeout=15)

    assert address_book is not None
    assert len(address_book) >= 0

    for node in address_book:
        assert node.registered_node_id >= 0
        for endpoint in node.service_endpoints:
            assert isinstance(
                endpoint,
                (BlockNodeServiceEndpoint, MirrorNodeServiceEndpoint, RpcRelayServiceEndpoint),
            )
