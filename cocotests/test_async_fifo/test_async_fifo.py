
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (
    RisingEdge, FallingEdge,
    Timer
)
from cocotb.handle import HierarchyObject as DUT

from queue import Queue
import random

from tqdm import tqdm
import time


FIFO_SIZE = 32
LOGIC_SIZE = 8
TEST_ITERS = 100

fifo = Queue(FIFO_SIZE)

async def reset_subr(dut : DUT):
    """Handle doing the reset input, waiting the appropriate clocks. 
    Then continuing. 
    """
    dut.i_rst_n.value = 0 
    await (RisingEdge(dut.i_wclk) or RisingEdge(dut.i_rclk))
    dut.i_rst_n.value = 1

async def write_subr(dut : DUT, w_data : int):
    """Handle write subroutine to aFIFO. Ignore the full flag."""
    await FallingEdge(dut.i_wclk)
    dut.i_wr.value = 1
    dut.i_wdata.value = w_data
    await RisingEdge(dut.i_wclk)
    dut.i_wr.value = 0
    dut.i_wdata.value = 0xbe

async def read_subr(dut : DUT) -> int:
    """Handle read subroutine to aFIFO. Ignore the empty flag."""
    await FallingEdge(dut.i_rclk)
    dut.i_rr.value = 1
    await RisingEdge(dut.i_rclk)
    dut.i_rr.value = 0

    # Done to ensure that reading is done for long enough when we return our o_rdata
    await FallingEdge(dut.i_rclk)
    
    return int(dut.o_rdata.value)

async def sync_subr(dut : DUT):
    """Wait long enough to ensure the synchronizers agree"""
    for i in range(3):
        await RisingEdge(dut.i_rclk)
        await RisingEdge(dut.i_wclk)

async def reset_test(dut : DUT):
    await reset_subr(dut)
    assert dut.o_rempty.value == 1 # it should be empty on reset

async def read_test(dut : DUT):
    """Assert read_data from our fifos. """

    # fifo will block if you read and it has no data
    if(not fifo.empty()):
        item = fifo.get()

        res = await read_subr(dut)
        # Wait for the synchronizers to sync
        dut.i_rr.value = 0
        await sync_subr(dut)
        assert item == res
    else:
        await flag_asserts(dut)

async def write_test(dut : DUT, write_data : int):
    """Write write_data to our fifos. """
    
    # fifo will block if you write and it has full data
    if(not fifo.full()):
        fifo.put(write_data)

        await write_subr(dut, write_data)
        # Wait for the synchronizers to sync
        dut.i_wr.value = 0
        await sync_subr(dut)
    else:
        await flag_asserts(dut)
        

async def rw_test(dut : DUT, write_data : int):
    # fifo will block if you read and it has no data
    if(not fifo.empty()):
        item = fifo.get()

        res = await read_subr(dut)
        dut.i_rr.value = 0
        assert item == res
    else:
        await flag_asserts(dut)
    
    # fifo will block if you write and it has full data
    if(not fifo.full()):
        fifo.put(write_data)

        await write_subr(dut, write_data)
    else: 
        await flag_asserts(dut)

    # Wait for the synchronizers to sync
    await sync_subr(dut)
    

async def flag_asserts(dut : DUT):
    assert dut.o_rempty.value == fifo.empty()
    assert dut.o_wfull.value == fifo.full()
    
@cocotb.test()
async def main_test(dut : DUT):
    # Setup Clocks
    cocotb.start_soon(Clock(dut.i_rclk, 13, units='ns').start())
    cocotb.start_soon(Clock(dut.i_wclk, 7, units='ns').start())

    # Setup Fake Queue to represent our actual queue...
    test_data = [random.randint(0x0, 2**LOGIC_SIZE - 1) for _ in range(TEST_ITERS)]

    # Initialize some initial values for the time being
    dut.i_rr.value = 0
    dut.i_wr.value = 0
    dut.i_wdata.value = 0x0

    # reset 
    await (RisingEdge(dut.i_wclk) or RisingEdge(dut.i_rclk))
    await reset_test(dut)

    # write
    for i in tqdm(range(0, TEST_ITERS//2), desc="Sole Write Tests"):
        await write_test(dut, test_data[i])
        await flag_asserts(dut)
    
    # read
    for i in tqdm(range(0, TEST_ITERS//2), desc="Sole Read Tests"):
        await read_test(dut)
        await flag_asserts(dut)

    # write/read
    for i in tqdm(range(TEST_ITERS//2, TEST_ITERS), desc="R&W Tests"):
        await rw_test(dut, test_data[i])
        await flag_asserts(dut)
