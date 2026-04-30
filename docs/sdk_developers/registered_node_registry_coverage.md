# Registered Node Registry Coverage in hiero-sdk-python

This document maps registered-node registry concepts to current SDK implementation status.

## Status Summary

The SDK implements the core registered-node registry surface that is present in
the current HAPI protobuf snapshot used by this repository. Remaining work is
primarily live-network proof coverage for the full create/update/delete and
consensus-node association matrix; those tests require an operator account
authorized to modify registered-node and consensus-node address book state.

## Covered Concepts

- `BlockNodeApi` enum: [src/hiero_sdk_python/address_book/block_node_api.py](../../src/hiero_sdk_python/address_book/block_node_api.py)
- `RegisteredServiceEndpoint` base type with IP/FQDN one-of validation:
  [src/hiero_sdk_python/address_book/registered_service_endpoint.py](../../src/hiero_sdk_python/address_book/registered_service_endpoint.py)
- Endpoint subtypes:
  - Block with one or more endpoint APIs: [src/hiero_sdk_python/address_book/block_node_service_endpoint.py](../../src/hiero_sdk_python/address_book/block_node_service_endpoint.py)
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
- Registered-node descriptions are validated against the HAPI 100 UTF-8
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
- End-to-end integration coverage for the registered-node lifecycle uses the
  standard integration environment and skips only when the live network rejects
  the configured operator with `UNAUTHORIZED`:
  [tests/integration/registered_node_transaction_e2e_test.py](../../tests/integration/registered_node_transaction_e2e_test.py)
- Live mirror query coverage uses the standard integration environment:
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

- Expand the registered-node lifecycle integration test into the full
  registered-node registry test matrix when a network with transaction support
  is available in CI.
- Add TCK coverage for registered-node create, update, delete, address-book
  query, and consensus-node association behavior.

## Example

- Registered node lifecycle example:
  [examples/nodes/registered_node_lifecycle.py](../../examples/nodes/registered_node_lifecycle.py)
