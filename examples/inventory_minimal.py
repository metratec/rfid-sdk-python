"""
This is a minimal example that shows reader object initialization,
runs a single inventory and prints the result.

Attention! You have to adapt the reader class to match your conditions.
"""

import asyncio
from metratec_rfid import RfidReaderException
# Attention! Change the reader class to match your device.
from metratec_rfid import DeskIdUhfv2


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
# Attention! Change the serial port according to your PC.
SERIAL_PORT = "COM41"  # "/dev/ttyUSB0"
# Attention! Change the reader class to match your device.
reader01 = DeskIdUhfv2("reader01", SERIAL_PORT)
asyncio.run(print_inventory(reader01))
