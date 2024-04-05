"""
This is a sample file for the metratec deskid uhf with the metratec rfid skd.

The program uses the connected deskid uhf reader on the serial port /dev/ttyUSB.

After connection it fetches the current inventory from the reader and prints it out

"""

import asyncio
from typing import List

from metratec_rfid import DeskIdUhf2
from metratec_rfid import UhfTag
from metratec_rfid import RfidReaderException


async def main():
    """_summary_
    """
    # Create an instance and define the serial connection
    reader = DeskIdUhf2(instance="Reader", serial_port="/dev/ttyACM0")
    # set a callback for the reader status
    reader.set_cb_status(lambda status: print(f"status changed: {status}"))
    # set a callback for the inventories
    reader.set_cb_inventory(lambda inventory: print(f"new inventory: {inventory}"))

    # connect the reader
    try:
        await reader.connect()
        # set the reader power
        await reader.set_power(4)

        # get the inventory
        inventory: List[UhfTag] = await reader.get_inventory()
        # print inventory
        print(f'Transponder found: {len(inventory)}')
        for tag in inventory:
            print(f'{tag.get_epc()}')

    except Exception as err:
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
