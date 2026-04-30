"""Live integration tests for RegisteredNodeAddressBookQuery against mirror REST APIs."""

from __future__ import annotations

import os

import pytest

from hiero_sdk_python import Client, RegisteredNodeAddressBookQuery
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


def _env_flag_enabled(name: str) -> bool:
    """Return whether a boolean-style env flag is enabled."""
    value = os.getenv(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


@pytest.mark.skipif(
    not _env_flag_enabled("ENABLE_LIVE_MIRROR_TESTS"),
    reason="Set ENABLE_LIVE_MIRROR_TESTS=true to run live mirror integration tests.",
)
def test_integration_registered_node_address_book_query_live_mirror():
    """Query should execute successfully against the live mirror registered-nodes endpoint."""
    client = Client.for_testnet()
    try:
        query = RegisteredNodeAddressBookQuery().set_limit(25).set_order("asc").add_registered_node_id_filter("gte", 0)

        address_book = query.execute(client, timeout=15)

        assert address_book is not None
        assert len(address_book) >= 0

        for node in address_book:
            assert node.registered_node_id >= 0
            for endpoint in node.service_endpoints:
                assert isinstance(
                    endpoint,
                    (BlockNodeServiceEndpoint, MirrorNodeServiceEndpoint, RpcRelayServiceEndpoint),
                )

    finally:
        client.close()
