"""
This is a sample file for the metratec deskid uhf with the metratec rfid sdk.

The program uses the connected deskid uhf reader on the serial port /dev/ttyUSB.

After connecting, the data of the current transponder is read out and overwritten.

"""

import asyncio
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
        await reader.set_power(4)

        # read the tag data
        response = await reader.read_tag_data(start=0, length=4)
        # print transponder data:
        inventory: List[UhfTag] = response['transponders']
        print(f'Transponder read: {len(inventory)}')
        for tag in inventory:
            print(f'{tag.get_epc()}: {tag.get_data()}')
        # check if some tags return an error
        errors: List[UhfTag] = response['errors']
        if len(errors):
            print(f'Read errors: {len(errors)}')
            for tag in errors:
                print(f'{tag.get_epc()}: Read error: {tag.get_error_message()}')

        # write the tag data
        response = await reader.write_tag_data(data="12345678", start=0)
        # list with successful written transponder
        inventory: List[UhfTag] = response['transponders']
        print(f'Transponder written: {len(inventory)}')
        for tag in inventory:
            print(f'{tag.get_epc()}: written with {tag.get_data()}')
        # check if some tags return an error
        errors: List[UhfTag] = response['errors']
        if len(errors):
            print(f'Write error: {len(errors)}')
            for tag in errors:
                print(f'{tag.get_epc()}: Write error: {tag.get_error_message()}')

    except Exception as err:
        print(f"Reader exception: {err}")
    finally:
        try:
            await reader.disconnect()
        except RfidReaderException as err:
            print(f"Error disconnect: {err}")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
