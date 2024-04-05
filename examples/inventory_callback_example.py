"""
This is a sample file for using the inventory callback methods in the library.

The program uses a deskid iso reader on the port COM1

After connecting, the continuous inventory is started and the tags found are printed to the console.
"""

import asyncio
import os
import sys

sys.path.append(os.getcwd())
# disable 'wrong-import-position' warning - pylint: disable=C0413
from metratec_rfid import DeskIdIso  # noqa -- flake ignore  pylint: disable=import-error
from metratec_rfid import RfidReaderException  # noqa -- flake ignore  pylint: disable=import-error


async def main():

    # Create an instance and define the serial connection
    reader = DeskIdIso(instance="Reader", serial_port="/dev/ttyUSB0")
    # set a callback for the reader status
    reader.set_cb_status(lambda status: print(f"status changed: {status}"))
    # set a callback for the inventories
    reader.set_cb_inventory(lambda inventory: print(f"new inventory: {inventory}"))

    # connect the reader
    try:
        await reader.connect()
        # start the inventory
        await reader.start_inventory()
        await asyncio.sleep(60)
        await reader.stop_inventory()

    except RfidReaderException as err:
        print(f"Reader exception: {err}")
    finally:
        try:
            await reader.disconnect()
        except RfidReaderException as err:
            print(f"Error disconnect: {err}")

    # Program finished

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
