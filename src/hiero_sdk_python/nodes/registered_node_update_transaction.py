"""
RegisteredNodeUpdateTransaction class for HIP-1137.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from google.protobuf.wrappers_pb2 import StringValue

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_update_pb2 import (
    RegisteredNodeUpdateTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)


@dataclass
class RegisteredNodeUpdateParams:
    """
    Parameters for updating a registered node.

    Attributes:
        registered_node_id (Optional[int]): The registered node ID to update.
        admin_key (Optional[PublicKey]): New administrative key for the node.
        description (Optional[str]): New description (max 100 UTF-8 bytes).
        service_endpoints (List[RegisteredServiceEndpoint]): New service endpoints (replaces previous, max 50).
        node_account (Optional[AccountId]): New account financially responsible for this node.
    """

    registered_node_id: Optional[int] = None
    admin_key: Optional[PublicKey] = None
    description: Optional[str] = None
    service_endpoints: List[RegisteredServiceEndpoint] = field(default_factory=list)
    node_account: Optional[AccountId] = None


class RegisteredNodeUpdateTransaction(Transaction):
    """
    A transaction to update an existing registered node in the network address book.

    This transaction, once complete, modifies the identified registered node
    state as requested. The existing admin_key MUST sign this transaction.
    """

    def __init__(self, params: Optional[RegisteredNodeUpdateParams] = None):
        super().__init__()
        params = params or RegisteredNodeUpdateParams()
        self.registered_node_id: Optional[int] = params.registered_node_id
        self.admin_key: Optional[PublicKey] = params.admin_key
        self.description: Optional[str] = params.description
        self.service_endpoints: List[RegisteredServiceEndpoint] = params.service_endpoints
        self.node_account: Optional[AccountId] = params.node_account

    def set_registered_node_id(self, registered_node_id: Optional[int]) -> "RegisteredNodeUpdateTransaction":
        self._require_not_frozen()
        self.registered_node_id = registered_node_id
        return self

    def set_admin_key(self, admin_key: Optional[PublicKey]) -> "RegisteredNodeUpdateTransaction":
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_description(self, description: Optional[str]) -> "RegisteredNodeUpdateTransaction":
        self._require_not_frozen()
        self.description = description
        return self

    def set_service_endpoints(
        self, service_endpoints: Optional[List[RegisteredServiceEndpoint]]
    ) -> "RegisteredNodeUpdateTransaction":
        self._require_not_frozen()
        self.service_endpoints = service_endpoints or []
        return self

    def set_node_account(self, node_account: Optional[AccountId]) -> "RegisteredNodeUpdateTransaction":
        self._require_not_frozen()
        self.node_account = node_account
        return self

    def _convert_to_proto(self, obj: Optional[Any]) -> Any:
        return obj._to_proto() if obj else None

    def _build_proto_body(self) -> RegisteredNodeUpdateTransactionBody:
        if self.registered_node_id is None:
            raise ValueError("Missing required registered_node_id")
        if self.service_endpoints and len(self.service_endpoints) > 50:
            raise ValueError("service_endpoints must not contain more than 50 entries")

        return RegisteredNodeUpdateTransactionBody(
            registered_node_id=self.registered_node_id,
            admin_key=self._convert_to_proto(self.admin_key),
            description=(
                StringValue(value=self.description)
                if self.description is not None
                else None
            ),
            service_endpoint=[
                endpoint._to_proto() for endpoint in self.service_endpoints or []
            ],
            node_account=self._convert_to_proto(self.node_account),
        )

    def build_transaction_body(self) -> TransactionBody:
        body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeUpdate.CopyFrom(body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeUpdate.CopyFrom(body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.address_book.updateRegisteredNode,
            query_func=None,
        )
