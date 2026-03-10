"""
RegisteredNodeCreateTransaction class for HIP-1137.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_create_pb2 import (
    RegisteredNodeCreateTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)


@dataclass
class RegisteredNodeCreateParams:
    """
    Parameters for creating a registered node.

    Attributes:
        admin_key (Optional[PublicKey]): Administrative key controlled by the node operator.
        description (Optional[str]): Short description of the node (max 100 UTF-8 bytes).
        service_endpoints (List[RegisteredServiceEndpoint]): Service endpoints for client calls (max 50).
        node_account (Optional[AccountId]): Account financially responsible for this registered node.
    """

    admin_key: Optional[PublicKey] = None
    description: Optional[str] = None
    service_endpoints: List[RegisteredServiceEndpoint] = field(default_factory=list)
    node_account: Optional[AccountId] = None


class RegisteredNodeCreateTransaction(Transaction):
    """
    A transaction to create a new registered node in the network address book.

    This transaction, once complete, adds a new registered node to the network state.
    The new registered node is visible and discoverable upon completion.

    The admin_key MUST sign this transaction.
    """

    def __init__(self, params: Optional[RegisteredNodeCreateParams] = None):
        super().__init__()
        params = params or RegisteredNodeCreateParams()
        self.admin_key: Optional[PublicKey] = params.admin_key
        self.description: Optional[str] = params.description
        self.service_endpoints: List[RegisteredServiceEndpoint] = params.service_endpoints
        self.node_account: Optional[AccountId] = params.node_account

    def set_admin_key(self, admin_key: Optional[PublicKey]) -> "RegisteredNodeCreateTransaction":
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_description(self, description: Optional[str]) -> "RegisteredNodeCreateTransaction":
        self._require_not_frozen()
        self.description = description
        return self

    def set_service_endpoints(
        self, service_endpoints: Optional[List[RegisteredServiceEndpoint]]
    ) -> "RegisteredNodeCreateTransaction":
        self._require_not_frozen()
        self.service_endpoints = service_endpoints or []
        return self

    def set_node_account(self, node_account: Optional[AccountId]) -> "RegisteredNodeCreateTransaction":
        self._require_not_frozen()
        self.node_account = node_account
        return self

    def _build_proto_body(self) -> RegisteredNodeCreateTransactionBody:
        if self.admin_key is None:
            raise ValueError("Missing required admin_key for RegisteredNodeCreateTransaction")
        if not self.service_endpoints:
            raise ValueError("service_endpoints must not be empty")
        if len(self.service_endpoints) > 50:
            raise ValueError("service_endpoints must not contain more than 50 entries")

        return RegisteredNodeCreateTransactionBody(
            admin_key=self.admin_key._to_proto() if self.admin_key else None,
            description=self.description,
            service_endpoint=[
                endpoint._to_proto() for endpoint in self.service_endpoints
            ],
            node_account=self.node_account._to_proto() if self.node_account else None,
        )

    def build_transaction_body(self) -> TransactionBody:
        body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeCreate.CopyFrom(body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeCreate.CopyFrom(body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.address_book.createRegisteredNode,
            query_func=None,
        )
