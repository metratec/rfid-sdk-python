"""
This is a minimal example that shows reader object initialization,
runs a single inventory and prints the result.

Attention! You have to adapt the reader class to match your conditions.
"""

import asyncio
from metratec_rfid import RfidReaderException
from example_utils import get_reader


async def print_inventory(reader):
    """Connect the reader, run a single inventory and print the result.
    """
    try:
        await reader.connect()
        print(await reader.get_inventory())
        await reader.disconnect()
    except RfidReaderException as e:
        print(e)


# Create a new reader object and run the example function.
reader01 = get_reader()
asyncio.run(print_inventory(reader01))
