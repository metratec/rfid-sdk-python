"""
This is a minimal example that shows automatic reader detection
and object initialization.
It runs a single inventory on each connected reader and prints the result.
"""

import asyncio
from metratec_rfid import RfidReaderException
from metratec_rfid import detect_readers


async def print_inventory():
    """Find connected readers, run a single inventory on each and print the result.
    """
    readers = await detect_readers()
    for port, reader in readers.items():
        print(f"Running example with {reader.__class__.__name__} on port {port}")
        try:
            await reader.connect()
            print(await reader.get_inventory())
            await reader.disconnect()
        except RfidReaderException as e:
            print(e)


# Run the example function on every reader connected to the system.
asyncio.run(print_inventory())