"""
Unit tests for the ContractUpdateTransaction class.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_update_transaction import (
    ContractUpdateParams,
    ContractUpdateTransaction,
)
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction


pytestmark = pytest.mark.unit


@pytest.fixture
def update_params(contract_id):
    """Fixture for contract update parameters."""
    return {
        "contract_id": contract_id,
        "memo": "Updated contract memo",
        "admin_key": PrivateKey.generate().public_key(),
        "auto_renew_period": Duration(7776000),  # 90 days
        "max_automatic_token_associations": 100,
        "auto_renew_account_id": AccountId(0, 0, 999),
        "staked_node_id": 5,
        "decline_reward": True,
    }


########### Constructor Tests ###########


def test_constructor_no_parameters():
    """Test creating a contract update transaction with no parameters."""
    tx = ContractUpdateTransaction()

    assert tx.contract_id is None
    assert tx.contract_memo is None
    assert tx.admin_key is None
    assert tx.auto_renew_period is None
    assert tx.max_automatic_token_associations is None
    assert tx.auto_renew_account_id is None
    assert tx.staked_node_id is None
    assert tx.decline_reward is None
    assert tx._default_transaction_fee == Hbar(20).to_tinybars()


def test_constructor_with_parameters(update_params):
    """Test creating a contract update transaction with constructor parameters."""
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params["max_automatic_token_associations"],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)

    assert tx.contract_id == update_params["contract_id"]
    assert tx.contract_memo == update_params["memo"]
    assert tx.admin_key == update_params["admin_key"]
    assert tx.auto_renew_period == update_params["auto_renew_period"]
    assert tx.max_automatic_token_associations == update_params["max_automatic_token_associations"]
    assert tx.auto_renew_account_id == update_params["auto_renew_account_id"]
    assert tx.staked_node_id == update_params["staked_node_id"]
    assert tx.decline_reward == update_params["decline_reward"]


########### Setter Method Tests ###########


def test_set_contract_id(contract_id):
    """Test setting contract ID."""
    tx = ContractUpdateTransaction()
    result = tx.set_contract_id(contract_id)

    assert tx.contract_id == contract_id
    assert result is tx  # Method chaining


def test_set_memo():
    """Test setting memo."""
    tx = ContractUpdateTransaction()
    memo = "Test contract memo"
    result = tx.set_contract_memo(memo)

    assert tx.contract_memo == memo
    assert result is tx  # Method chaining


def test_set_admin_key():
    """Test setting admin key."""
    tx = ContractUpdateTransaction()
    admin_key = PrivateKey.generate().public_key()
    result = tx.set_admin_key(admin_key)

    assert tx.admin_key == admin_key
    assert result is tx  # Method chaining


def test_set_auto_renew_period():
    """Test setting auto renew period."""
    tx = ContractUpdateTransaction()
    auto_renew_period = Duration(7776000)
    result = tx.set_auto_renew_period(auto_renew_period)

    assert tx.auto_renew_period == auto_renew_period
    assert result is tx  # Method chaining


def test_set_max_automatic_token_associations():
    """Test setting max automatic token associations."""
    tx = ContractUpdateTransaction()
    max_associations = 100
    result = tx.set_max_automatic_token_associations(max_associations)

    assert tx.max_automatic_token_associations == max_associations
    assert result is tx  # Method chaining


def test_set_auto_renew_account_id():
    """Test setting auto renew account ID."""
    tx = ContractUpdateTransaction()
    auto_renew_account_id = AccountId(0, 0, 999)
    result = tx.set_auto_renew_account_id(auto_renew_account_id)

    assert tx.auto_renew_account_id == auto_renew_account_id
    assert result is tx  # Method chaining


def test_set_staked_node_id():
    """Test setting staked node ID clears an existing staked account ID."""
    tx = ContractUpdateTransaction()
    staked_account_id = AccountId(0, 0, 999)
    tx.set_staked_account_id(staked_account_id)

    staked_node_id = 5
    result = tx.set_staked_node_id(staked_node_id)

    assert tx.staked_node_id == staked_node_id
    assert tx.staked_account_id is None
    assert result is tx  # Method chaining


def test_set_staked_node_id_to_none_preserves_staked_account_id():
    """Test that setting staked node ID to None preserves the staked account ID."""
    tx = ContractUpdateTransaction()
    staked_account_id = AccountId(0, 0, 999)
    tx.set_staked_account_id(staked_account_id)

    result = tx.set_staked_node_id(None)

    assert tx.staked_node_id is None
    assert tx.staked_account_id == staked_account_id
    assert result is tx  # Method chaining


def test_set_decline_reward():
    """Test setting decline reward."""
    tx = ContractUpdateTransaction()
    decline_reward = True
    result = tx.set_decline_reward(decline_reward)

    assert tx.decline_reward == decline_reward
    assert result is tx  # Method chaining


def test_set_auto_renew_account_id_to_zero():
    """Test setting auto renew account ID to the 0.0.0 clearing sentinel."""
    tx = ContractUpdateTransaction()
    result = tx.set_auto_renew_account_id(AccountId(0, 0, 0))

    assert tx.auto_renew_account_id == AccountId(0, 0, 0)
    assert result is tx  # Method chaining


def test_set_staked_account_id():
    """Test setting a valid staked account ID clears an existing staked node ID."""
    tx = ContractUpdateTransaction()
    tx.set_staked_node_id(5)

    staked_account_id = AccountId(0, 0, 999)
    result = tx.set_staked_account_id(staked_account_id)

    assert tx.staked_account_id == staked_account_id
    assert tx.staked_node_id is None
    assert result is tx  # Method chaining


def test_set_staked_account_id_to_none_preserves_staked_node_id():
    """Test that setting staked account ID to None preserves the staked node ID."""
    tx = ContractUpdateTransaction()
    staked_node_id = 5
    tx.set_staked_node_id(staked_node_id)

    result = tx.set_staked_account_id(None)

    assert tx.staked_account_id is None
    assert tx.staked_node_id == staked_node_id
    assert result is tx  # Method chaining


def test_set_staked_account_id_to_zero():
    """Test setting staked account ID to 0.0.0 clears staking."""
    tx = ContractUpdateTransaction()

    result = tx.set_staked_account_id(AccountId(0, 0, 0))

    assert tx.staked_account_id == AccountId(0, 0, 0)
    assert tx.staked_node_id is None
    assert result is tx  # Method chaining


########### Method Chaining Tests ###########


def test_method_chaining(update_params):
    """Test that all setter methods can be chained together."""
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(update_params["contract_id"])
        .set_contract_memo(update_params["memo"])
        .set_admin_key(update_params["admin_key"])
        .set_auto_renew_period(update_params["auto_renew_period"])
        .set_max_automatic_token_associations(update_params["max_automatic_token_associations"])
        .set_auto_renew_account_id(update_params["auto_renew_account_id"])
        .set_staked_node_id(update_params["staked_node_id"])
        .set_decline_reward(update_params["decline_reward"])
    )

    assert tx.contract_id == update_params["contract_id"]
    assert tx.contract_memo == update_params["memo"]
    assert tx.admin_key == update_params["admin_key"]
    assert tx.auto_renew_period == update_params["auto_renew_period"]
    assert tx.max_automatic_token_associations == update_params["max_automatic_token_associations"]
    assert tx.auto_renew_account_id == update_params["auto_renew_account_id"]
    assert tx.staked_node_id == update_params["staked_node_id"]
    assert tx.decline_reward == update_params["decline_reward"]


########### Transaction Body Building Tests ###########


def test_build_transaction_body_success(contract_id, mock_account_ids, transaction_id):
    """Test building transaction body with valid contract ID."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = ContractUpdateTransaction()
    tx.set_contract_id(contract_id)
    tx.set_contract_memo("Test memo")
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    transaction_body = tx.build_transaction_body()

    assert transaction_body.contractUpdateInstance.contractID.contractNum == contract_id.contract
    assert transaction_body.contractUpdateInstance.contractID.shardNum == contract_id.shard
    assert transaction_body.contractUpdateInstance.contractID.realmNum == contract_id.realm


@pytest.mark.parametrize(
    "admin_key",
    [
        PrivateKey.generate(),
        KeyList([PrivateKey.generate().public_key(), PrivateKey.generate().public_key()]),
    ],
    ids=["private-key", "key-list"],
)
def test_build_proto_body_with_generic_admin_key(contract_id, admin_key):
    """Test building a contract update body with generic admin key types."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_admin_key(admin_key)

    proto_body = tx._build_proto_body()

    assert tx.admin_key is admin_key
    assert proto_body.adminKey == admin_key.to_proto_key()


def test_build_transaction_body_missing_contract_id(mock_account_ids, transaction_id):
    """Test building transaction body without contract ID omits the field."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = ContractUpdateTransaction()
    tx.set_contract_memo("Test memo")
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    transaction_body = tx.build_transaction_body()

    assert not transaction_body.contractUpdateInstance.HasField("contractID")


def test_build_transaction_body_with_all_parameters(update_params, mock_account_ids, transaction_id):
    """Test building transaction body with all parameters set."""
    _, _, node_account_id, _, _ = mock_account_ids

    # Create transaction with basic parameters to avoid protobuf constructor issues
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params["max_automatic_token_associations"],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    transaction_body = tx.build_transaction_body()

    # Verify contract ID is set
    assert transaction_body.contractUpdateInstance.contractID.contractNum == update_params["contract_id"].contract
    assert transaction_body.contractUpdateInstance.contractID.shardNum == update_params["contract_id"].shard
    assert transaction_body.contractUpdateInstance.contractID.realmNum == update_params["contract_id"].realm

    # Verify other fields are present (the actual protobuf structure may vary)
    assert transaction_body.contractUpdateInstance.HasField("contractID")


def test_build_scheduled_body_with_all_parameters(update_params, mock_account_ids, transaction_id):
    """Test building schedulable transaction body with all parameters set."""
    _, _, node_account_id, _, _ = mock_account_ids

    # Create transaction with all parameters
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params["max_automatic_token_associations"],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    schedulable_body = tx.build_scheduled_body()

    # Verify correct return type
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with contract update type
    assert schedulable_body.HasField("contractUpdateInstance")

    # Verify contract ID is set
    assert schedulable_body.contractUpdateInstance.contractID.contractNum == update_params["contract_id"].contract
    assert schedulable_body.contractUpdateInstance.contractID.shardNum == update_params["contract_id"].shard
    assert schedulable_body.contractUpdateInstance.contractID.realmNum == update_params["contract_id"].realm


def test_build_proto_body_with_cleared_fields(contract_id):
    """Test building a contract update body with cleared auto-renew and staked accounts."""
    tx = ContractUpdateTransaction()
    tx.set_contract_id(contract_id)
    tx.set_auto_renew_account_id(AccountId(0, 0, 0))
    tx.set_staked_account_id(AccountId(0, 0, 0))

    proto_body = tx._build_proto_body()

    # Auto-renew clearing must use an empty AccountID with no account oneof.
    assert proto_body.HasField("auto_renew_account_id")
    assert proto_body.auto_renew_account_id.WhichOneof("account") is None
    assert proto_body.auto_renew_account_id.SerializeToString() == b""

    # Staking clearing must explicitly select accountNum with a value of zero.
    assert proto_body.HasField("staked_account_id")
    assert proto_body.staked_account_id.WhichOneof("account") == "accountNum"
    assert proto_body.staked_account_id.accountNum == 0


def test_build_proto_body_rejects_conflicting_staking_targets(contract_id):
    """Test that constructor parameters cannot specify both staking targets."""
    params = ContractUpdateParams(
        contract_id=contract_id,
        staked_account_id=AccountId(0, 0, 999),
        staked_node_id=5,
    )
    tx = ContractUpdateTransaction(contract_params=params)

    with pytest.raises(
        ValueError,
        match="Specify either staked_node_id or staked_account_id, not both",
    ):
        tx._build_proto_body()


########### Transaction Execution Tests ###########


def test_transaction_immutability_concept(contract_id):
    """Test that the transaction can track if it should be frozen (conceptual test)."""
    tx = ContractUpdateTransaction()
    tx.set_contract_id(contract_id)

    # Verify transaction can be created and modified normally
    tx.set_contract_memo("Initial memo")
    assert tx.contract_memo == "Initial memo"

    # Verify we can change memo again (since it's not frozen)
    tx.set_contract_memo("Updated memo")
    assert tx.contract_memo == "Updated memo"


########### Minimal Operations Tests ###########


def test_memo_only_update(contract_id):
    """Test updating only the memo field."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_contract_memo("New memo only")

    assert tx.contract_id == contract_id
    assert tx.contract_memo == "New memo only"
    assert tx.admin_key is None


def test_admin_key_only_update(contract_id):
    """Test updating only the admin key field."""
    new_admin_key = PrivateKey.generate().public_key()
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_admin_key(new_admin_key)

    assert tx.contract_id == contract_id
    assert tx.admin_key.to_string() == new_admin_key.to_string()
    assert tx.contract_memo is None


def test_multiple_field_update(contract_id):
    """Test updating multiple fields together."""
    new_admin_key = PrivateKey.generate().public_key()
    new_memo = "Multiple fields updated"
    new_max_associations = 50

    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_admin_key(new_admin_key)
        .set_contract_memo(new_memo)
        .set_max_automatic_token_associations(new_max_associations)
    )

    assert tx.contract_id == contract_id
    assert tx.admin_key == new_admin_key
    assert tx.contract_memo == new_memo
    assert tx.max_automatic_token_associations == new_max_associations


########### Edge Cases Tests ###########


def test_empty_memo(contract_id):
    """Test setting an empty memo."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_contract_memo("")

    assert tx.contract_memo == ""


def test_very_long_memo(contract_id):
    """Test setting a very long memo."""
    long_memo = "x" * 1000  # 1000 character memo
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_contract_memo(long_memo)

    assert tx.contract_memo == long_memo


def test_zero_max_automatic_token_associations(contract_id):
    """Test setting max automatic token associations to zero."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_max_automatic_token_associations(0)

    assert tx.max_automatic_token_associations == 0


def test_negative_staked_node_id(contract_id):
    """Test setting a negative staked node ID."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_staked_node_id(-1)

    assert tx.staked_node_id == -1


def test_decline_reward_false(contract_id):
    """Test setting decline reward to False."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_decline_reward(False)

    assert tx.decline_reward is False


def _round_trip(tx, transaction_id):
    """Freeze a transaction, serialize it and deserialize it again."""
    tx.set_transaction_id(transaction_id)
    tx.set_node_account_ids([AccountId(0, 0, 3)])
    tx.freeze()
    tx_bytes = tx.to_bytes()
    return tx_bytes, Transaction.from_bytes(tx_bytes)


def test_from_bytes_restores_all_fields(transaction_id, contract_id):
    """Test that from_bytes restores every field set with a staked account."""
    admin_key = PrivateKey.generate_ed25519().public_key()
    tx = ContractUpdateTransaction(
        ContractUpdateParams(
            contract_id=contract_id,
            expiration_time=Timestamp(1_800_000_000, 42),
            admin_key=admin_key,
            auto_renew_period=Duration(7_000_000),
            contract_memo="round trip",
            max_automatic_token_associations=10,
            auto_renew_account_id=AccountId(0, 0, 12),
            staked_account_id=AccountId(0, 0, 13),
            decline_reward=False,
        )
    )

    tx_bytes, restored = _round_trip(tx, transaction_id)

    assert isinstance(restored, ContractUpdateTransaction)
    assert restored.contract_id == contract_id
    assert restored.expiration_time == Timestamp(1_800_000_000, 42)
    assert restored.admin_key.to_bytes_raw() == admin_key.to_bytes_raw()
    assert restored.auto_renew_period == Duration(7_000_000)
    assert restored.contract_memo == "round trip"
    assert restored.max_automatic_token_associations == 10
    assert restored.auto_renew_account_id == AccountId(0, 0, 12)
    assert restored.staked_account_id == AccountId(0, 0, 13)
    assert restored.staked_node_id is None
    assert restored.decline_reward is False
    assert restored.to_bytes() == tx_bytes


def test_from_bytes_preserves_zero_and_empty_values(transaction_id, contract_id):
    """Test that zero and empty values on presence-tracked fields are not mistaken for unset."""
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_contract_memo("")
        .set_max_automatic_token_associations(0)
        .set_staked_node_id(0)
    )

    _, restored = _round_trip(tx, transaction_id)

    assert restored.contract_memo == ""
    assert restored.max_automatic_token_associations == 0
    assert restored.staked_node_id == 0
    assert restored.staked_account_id is None


def test_from_bytes_restores_clear_sentinels(transaction_id, contract_id):
    """Test that the 0.0.0 clear sentinels for auto-renew and staked accounts survive a round trip."""
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_auto_renew_account_id(AccountId(0, 0, 0))
        .set_staked_account_id(AccountId(0, 0, 0))
    )

    tx_bytes, restored = _round_trip(tx, transaction_id)

    assert restored.auto_renew_account_id == AccountId(0, 0, 0)
    assert restored.staked_account_id == AccountId(0, 0, 0)
    assert restored.to_bytes() == tx_bytes


def test_from_bytes_with_unset_fields(transaction_id, contract_id):
    """Test that fields left unset come back as None."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id)

    _, restored = _round_trip(tx, transaction_id)

    assert restored.contract_id == contract_id
    assert restored.expiration_time is None
    assert restored.admin_key is None
    assert restored.auto_renew_period is None
    assert restored.contract_memo is None
    assert restored.max_automatic_token_associations is None
    assert restored.auto_renew_account_id is None
    assert restored.staked_account_id is None
    assert restored.staked_node_id is None
    assert restored.decline_reward is None


def test_from_protobuf_reads_deprecated_memo_arm(transaction_id, contract_id):
    """Test that a memo sent in the deprecated plain-string arm of memoField is restored."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id)
    tx.set_transaction_id(transaction_id)
    tx.set_node_account_ids([AccountId(0, 0, 3)])
    body = tx.build_transaction_body()
    body.contractUpdateInstance.memo = "legacy memo"

    restored = ContractUpdateTransaction._from_protobuf(body, body.SerializeToString(), None)

    assert restored.contract_memo == "legacy memo"
