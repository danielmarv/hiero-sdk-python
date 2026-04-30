# HIP-1137 Coverage in hiero-sdk-python

This document maps HIP-1137 concepts to current SDK implementation status.

## Status Summary

The SDK implements the HIP-1137 surface that is present in the current HAPI
protobuf snapshot used by this repository. The remaining HIP gap is
`nodeAccountId` on registered-node create, update, and read models. The linked
HIP includes that field, but the local `.protos` inputs and generated Python
protobufs do not currently define it:

- [.protos/services/registered_node_create.proto](../../.protos/services/registered_node_create.proto)
- [.protos/services/registered_node_update.proto](../../.protos/services/registered_node_update.proto)
- [.protos/services/state/addressbook/registered_node.proto](../../.protos/services/state/addressbook/registered_node.proto)

Do not add SDK serialization for `nodeAccountId` with guessed protobuf field
numbers. Complete that field only after the upstream HAPI protobufs define it,
then regenerate with `uv run python generate_proto.py`.

## Covered Concepts

- `BlockNodeApi` enum: [src/hiero_sdk_python/address_book/block_node_api.py](../../src/hiero_sdk_python/address_book/block_node_api.py)
- `RegisteredServiceEndpoint` base type with IP/FQDN one-of validation:
  [src/hiero_sdk_python/address_book/registered_service_endpoint.py](../../src/hiero_sdk_python/address_book/registered_service_endpoint.py)
- Endpoint subtypes:
  - Block: [src/hiero_sdk_python/address_book/block_node_service_endpoint.py](../../src/hiero_sdk_python/address_book/block_node_service_endpoint.py)
  - Mirror: [src/hiero_sdk_python/address_book/mirror_node_service_endpoint.py](../../src/hiero_sdk_python/address_book/mirror_node_service_endpoint.py)
  - RPC relay: [src/hiero_sdk_python/address_book/rpc_relay_service_endpoint.py](../../src/hiero_sdk_python/address_book/rpc_relay_service_endpoint.py)
  - General service: [src/hiero_sdk_python/address_book/general_service_endpoint.py](../../src/hiero_sdk_python/address_book/general_service_endpoint.py)
- Registered node transactions:
  - Create: [src/hiero_sdk_python/nodes/registered_node_create_transaction.py](../../src/hiero_sdk_python/nodes/registered_node_create_transaction.py)
  - Update: [src/hiero_sdk_python/nodes/registered_node_update_transaction.py](../../src/hiero_sdk_python/nodes/registered_node_update_transaction.py)
  - Delete: [src/hiero_sdk_python/nodes/registered_node_delete_transaction.py](../../src/hiero_sdk_python/nodes/registered_node_delete_transaction.py)
- Registered-node `adminKey` accepts and round-trips generic SDK `Key` values,
  including `KeyList` and threshold keys. Empty `KeyList` admin keys are
  rejected.
- Registered-node descriptions are validated against the HIP/HAPI 100 UTF-8
  byte limit.
- `TransactionReceipt.registered_node_id`:
  [src/hiero_sdk_python/transaction/transaction_receipt.py](../../src/hiero_sdk_python/transaction/transaction_receipt.py)
- Consensus node association fields:
  - Create: [src/hiero_sdk_python/nodes/node_create_transaction.py](../../src/hiero_sdk_python/nodes/node_create_transaction.py)
  - Update (including clear semantics): [src/hiero_sdk_python/nodes/node_update_transaction.py](../../src/hiero_sdk_python/nodes/node_update_transaction.py)
- Registered-node response codes (public SDK enum):
  - [src/hiero_sdk_python/response_code.py](../../src/hiero_sdk_python/response_code.py)
- Registered node read models:
  - [src/hiero_sdk_python/address_book/registered_node.py](../../src/hiero_sdk_python/address_book/registered_node.py)
  - [src/hiero_sdk_python/address_book/registered_node_address_book.py](../../src/hiero_sdk_python/address_book/registered_node_address_book.py)

## Mirror Query Support

- `RegisteredNodeAddressBookQuery` execution is implemented using mirror-node REST APIs (`/api/v1/network/registered-nodes`), including pagination and filter support:
  [src/hiero_sdk_python/address_book/registered_node_address_book_query.py](../../src/hiero_sdk_python/address_book/registered_node_address_book_query.py)
- End-to-end integration coverage for the registered-node lifecycle remains gated on environment/network support in CI:
  [tests/integration/registered_node_transaction_e2e_test.py](../../tests/integration/registered_node_transaction_e2e_test.py)
- Live mirror query coverage is opt-in with `ENABLE_LIVE_MIRROR_TESTS=true`:
  [tests/integration/registered_node_address_book_query_e2e_test.py](../../tests/integration/registered_node_address_book_query_e2e_test.py)

## Tests

- Endpoint tests (including general subtype when protobuf supports it):
  [tests/unit/registered_service_endpoint_test.py](../../tests/unit/registered_service_endpoint_test.py)
- Registered-node transaction tests:
  - [tests/unit/registered_node_create_transaction_test.py](../../tests/unit/registered_node_create_transaction_test.py)
  - [tests/unit/registered_node_update_transaction_test.py](../../tests/unit/registered_node_update_transaction_test.py)
  - [tests/unit/registered_node_delete_transaction_test.py](../../tests/unit/registered_node_delete_transaction_test.py)
- Node association tests:
  - [tests/unit/node_create_transaction_test.py](../../tests/unit/node_create_transaction_test.py)
  - [tests/unit/node_update_transaction_test.py](../../tests/unit/node_update_transaction_test.py)
- Receipt field test:
  [tests/unit/transaction_receipt_test.py](../../tests/unit/transaction_receipt_test.py)

## Remaining Work

- Add `nodeAccountId` support to `RegisteredNodeCreateTransaction`,
  `RegisteredNodeUpdateTransaction`, and `RegisteredNode` after the upstream
  HAPI protobufs define that field.
- Expand the skipped registered-node lifecycle integration test into the full
  HIP test matrix when a network with HIP-1137 transaction support is available
  in CI.

## Example

- Registered node lifecycle example:
  [examples/nodes/registered_node_lifecycle.py](../../examples/nodes/registered_node_lifecycle.py)
