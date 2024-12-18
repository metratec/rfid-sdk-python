"""
This is a sample file for the Metratec DeskID UHF using the metratec_rfid SDK.

The program uses the connected DeskID UHF reader on the serial port /dev/ttyUSB0.
Note: You may have to change this according to your PC.

After connecting, the EPC of the current transponder is overwritten.

"""

import asyncio
import json
from typing import List

from metratec_rfid import DeskIdUhf
from metratec_rfid import UhfTag
from metratec_rfid import RfidReaderException


async def main():

    # Create an instance and define the serial connection
    reader = DeskIdUhf(instance="Reader", serial_port="/dev/ttyUSB0")
    # set a callback for the reader status
    reader.set_cb_status(lambda status: print(f"status changed: {status}"))
    # set a callback for the inventories
    reader.set_cb_inventory(lambda inventory: print(f"new inventory: {inventory}"))

    # connect the reader
    try:
        await reader.connect()
        # set the reader power
        await reader.set_power(10)

        # write the tag epc
        response = await reader.write_tag_epc(new_epc="A001B002C003D004")
        # list with successful written transponder
        inventory: List[UhfTag] = response['transponders']
        print(f'EPC written: {len(inventory)}')
        for tag in inventory:
            print(json.dumps(tag))
            # print(f'EPC changed from {tag["old_epc"]}: to {tag.get_epc()}')
        # check if some tags return an error
        errors: List[UhfTag] = response['errors']
        if len(errors):
            print(f'EPC write error: {len(errors)}')
            for tag in errors:
                print(f'{tag.get_epc()}: EPC write error: {tag.get_error_message()}')

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
