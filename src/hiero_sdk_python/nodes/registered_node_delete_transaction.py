"""
RegisteredNodeDeleteTransaction class for HIP-1137.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_delete_pb2 import (
    RegisteredNodeDeleteTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


class RegisteredNodeDeleteTransaction(Transaction):
    """
    A transaction to remove a registered node from the network address book.

    This transaction, once complete, removes the identified registered node
    from the network state. Must be signed by the existing admin_key or
    authorized by the Hiero network governance structure.
    """

    def __init__(self, registered_node_id: Optional[int] = None):
        super().__init__()
        self.registered_node_id: Optional[int] = registered_node_id

    def set_registered_node_id(
        self, registered_node_id: Optional[int]
    ) -> "RegisteredNodeDeleteTransaction":
        self._require_not_frozen()
        self.registered_node_id = registered_node_id
        return self

    def _build_proto_body(self) -> RegisteredNodeDeleteTransactionBody:
        if self.registered_node_id is None:
            raise ValueError("Missing required registered_node_id")

        return RegisteredNodeDeleteTransactionBody(
            registered_node_id=self.registered_node_id,
        )

    def build_transaction_body(self) -> TransactionBody:
        body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeDelete.CopyFrom(body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeDelete.CopyFrom(body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.address_book.deleteRegisteredNode,
            query_func=None,
        )
