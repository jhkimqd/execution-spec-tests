"""
Test cases for deploying a contract and calling it in the same block.
"""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types import compute_create_address


@pytest.mark.valid_from("London")
def test_deploy_and_call_same_block_state_test(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test deploying a contract and calling it in the same transaction using CREATE opcode.
    This is a state test that demonstrates contract creation and immediate execution.
    """
    env = Environment()

    # Simple contract that stores a value and can return it
    deployed_contract_code = (
        Op.CALLDATASIZE
        + Op.ISZERO
        + Op.PUSH1(0x20)  # Jump destination for storage operation
        + Op.JUMPI
        +
        # Return stored value (when calldata is empty)
        Op.PUSH1(0)  # Storage slot 0
        + Op.SLOAD  # Load from storage
        + Op.PUSH1(0)  # Memory offset
        + Op.MSTORE  # Store in memory
        + Op.PUSH1(0x20)  # Return 32 bytes
        + Op.PUSH1(0)  # From memory offset 0
        + Op.RETURN
        +
        # Store value (when calldata is provided) - JUMPDEST at 0x20
        Op.JUMPDEST
        + Op.PUSH1(0)  # Calldata offset
        + Op.CALLDATALOAD  # Load 32 bytes from calldata
        + Op.PUSH1(0)  # Storage slot 0
        + Op.SSTORE  # Store to storage slot 0
        + Op.STOP
    )

    # Factory contract that deploys the above contract and immediately calls it
    factory_code = (
        # Deploy the contract
        Op.PUSH1(len(deployed_contract_code))  # Code size
        + Op.PUSH1(0x40)  # Code offset in memory (after this factory code)
        + Op.PUSH1(0)  # Memory offset where code is stored
        + Op.CODECOPY  # Copy contract code to memory
        + Op.PUSH1(len(deployed_contract_code))  # Code size
        + Op.PUSH1(0)  # Memory offset
        + Op.PUSH1(0)  # Value to send
        + Op.CREATE  # Deploy contract, returns address on stack
        +
        # Store the deployed contract address for later verification
        Op.DUP1  # Duplicate contract address
        + Op.PUSH1(1)  # Storage slot 1
        + Op.SSTORE  # Store contract address
        +
        # Prepare call data (store value 42)
        Op.PUSH1(0x2A)  # Value to store
        + Op.PUSH1(0)  # Memory offset
        + Op.MSTORE  # Store value in memory as calldata
        +
        # Call the deployed contract to store the value
        Op.PUSH1(0)  # Return data size
        + Op.PUSH1(0)  # Return data offset
        + Op.PUSH1(0x20)  # Args size (32 bytes)
        + Op.PUSH1(0)  # Args offset
        + Op.PUSH1(0)  # Value to send
        + Op.DUP6  # Contract address (duplicated earlier)
        + Op.GAS  # Gas to send
        + Op.CALL  # Make the call
        +
        # Store call result
        Op.PUSH1(2)  # Storage slot 2
        + Op.SSTORE  # Store call success (1) or failure (0)
        +
        # Call the contract again to read the stored value
        Op.PUSH1(0x20)  # Return data size
        + Op.PUSH1(0x00)  # Return data offset (changed from 0x60)
        + Op.PUSH1(0)  # Args size (0 bytes - no calldata for read)
        + Op.PUSH1(0)  # Args offset
        + Op.PUSH1(0)  # Value to send
        + Op.DUP6  # Contract address
        + Op.GAS  # Gas to send
        + Op.CALL  # Make the call
        +
        # Store the returned value
        Op.PUSH1(0x00)  # Memory offset where return data was stored (changed from 0x60)
        + Op.MLOAD  # Load the returned value
        + Op.PUSH1(3)  # Storage slot 3
        + Op.SSTORE  # Store the returned value
        + Op.STOP
        +
        # Append the deployed contract code
        deployed_contract_code
    )

    # Deploy factory contract
    factory_address = pre.deploy_contract(factory_code)
    print(f"factory_address: {factory_address}")

    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=factory_address,
        gas_price=1100000,
        gas_limit=15000000,
    )

    # Calculate the expected deployed contract address
    # Contract created by factory with nonce 1 (since factory starts with nonce 1)

    expected_deployed_address = compute_create_address(address=factory_address, nonce=1)
    print(f"expected_deployed_address: {expected_deployed_address}")

    # Expected state after execution
    post = {
        factory_address: Account(
            storage={
                # Slot 1: Should contain the deployed contract address
                1: expected_deployed_address,
                # Slot 2: Should be 1 (call success)
                2: 1,
                # Slot 3: Should be 42 (the value we stored and retrieved)
                3: 42,
            }
        )
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
