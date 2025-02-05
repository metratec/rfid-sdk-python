"""
This is a sample file for the metratec deskid uhf with the metratec rfid skd.

The program uses the connected deskid uhf reader on the serial port /dev/ttyUSB.

After connection it fetches the current inventory from the reader and prints it out

"""

import asyncio
from typing import List

from metratec_rfid import DeskIdNfc
from metratec_rfid.hf_tag import HfTag
from metratec_rfid import RfidReaderException
from metratec_rfid.nfc_reader_at import NfcMode


async def main():
    """_summary_
    """
    # Create an instance and define the serial connection
    reader = DeskIdNfc(instance="Reader", serial_port="/dev/ttyACM0")
    # set a callback for the reader status
    reader.set_cb_status(lambda status: print(f"status changed: {status}"))
    # set a callback for the inventories
    reader.set_cb_inventory(lambda inventory: print(f"new inventory: {inventory}"))

    # connect the reader
    try:
        await reader.connect()
        # per default the reader can read ISO15 and ISO14A transponder
        # if you not know with type of transponder you have, you can call the detect_tag_types() method
        inventory: List[HfTag] = await reader.detect_tag_types()
        # print inventory with transponder type
        print(f'Transponder found: {len(inventory)}')
        for tag in inventory:
            print(f'{tag.get_type()} - {tag.get_id()}')

        # then you can set the mode reader in the mode you need
        await reader.set_mode(NfcMode.ISO14A)
        # call the inventory
        inventory: List[HfTag] = await reader.get_inventory()
        # print inventory
        print(f'Transponder found: {len(inventory)}')
        for tag in inventory:
            print(f'{tag.get_id()}')

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
