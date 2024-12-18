"""
This is a sample file for the metratec deskid uhf with the metratec rfid sdk.

The program uses the connected deskid uhf reader on the serial port /dev/ttyUSB.

After connecting, the data of the current transponder is read out and overwritten.

"""

import asyncio
from typing import List

from metratec_rfid import UhfTag
from metratec_rfid import RfidReaderException
from example_utils import get_uhf_reader


async def read_tid(reader):
    response: List[UhfTag] = await reader.read_tag_tid(start=0, length=4)
    if len(response) == 0:
        print("Reading TID found 0 transponders.")
        return None
    
    print("Read result:")
    first_success = None
    for tag in response:
        if tag.has_error():
            print(f'EPC: {tag.get_epc()}, Error: {tag.get_error_message()}')
        else:
            print(f'EPC: {tag.get_epc()}, TID: {tag.get_data()}')
            first_success = tag if first_success is None else None

    return first_success.get_tid()


async def write_epc(reader, tid):
    new_epc = "12345678"

    print(f"Write {new_epc} into EPC of tag with TID {tid} ...")

    response = await reader.write_tag_epc(tid, new_epc, start=0)
    if len(response) == 0:
        print("Writing EPC found 0 transponders.")
        return None

    for tag in response:
        if tag.has_error():
            print(f'EPC: {tag.get_epc()}, Error: {tag.get_error_message()}')
        else:
            print(f'EPC: {tag.get_epc()}, Success')


async def main():
    # Create a reader instance from commandline arguments.
    reader = get_uhf_reader()

    try:
        # Connect the reader.
        await reader.connect()
        # Get the tag ID of the first responding transponder.
        tid = await read_tid(reader)
        # Write a new EPC value.
        if tid is not None:
            await write_epc(reader, tid)
    except RfidReaderException as err:
        print(f"Reader exception: {err}")
    finally:
        # Disconnect the reader for clean shutdown.
        try:
            await reader.disconnect()
        except RfidReaderException as err:
            print(f"Disconnect error: {err}")


if __name__ == '__main__':
    asyncio.run(main())
