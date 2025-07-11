"""
abstract: Tests [EIP-1344: CHAINID opcode](https://eips.ethereum.org/EIPS/eip-1344)
    Test cases for [EIP-1344: CHAINID opcode](https://eips.ethereum.org/EIPS/eip-1344).
"""

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1344.md"
REFERENCE_SPEC_VERSION = "02e46aebc80e6e5006ab4d2daa41876139f9a9e2"


@pytest.mark.valid_from("Istanbul")
def test_chainid(state_test: StateTestFiller, pre: Alloc):
    """Test CHAINID opcode."""
    env = Environment(
        fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=10000000000,
        number=1,
        timestamp=1000,
    )

    contract_address = pre.deploy_contract(Op.SSTORE(1, Op.CHAINID) + Op.STOP)
    sender = pre.fund_eoa()

    tx = Transaction(
        ty=0x0,
        # chain_id=0x301824, # 3151908
        chain_id=0x20D5E4,  # 2151908
        to=contract_address,
        gas_price=1100000,
        gas_limit=15000000,
        sender=sender,
    )

    # Log transaction details
    print(f"Transaction: {tx}")
    print(f"Chain ID: {hex(tx.chain_id)}")
    print(f"Contract address: {contract_address}")

    post = {
        # contract_address: Account(storage={"0x01": "0x301824"}),
        contract_address: Account(storage={"0x01": "0x20D5E4"}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
