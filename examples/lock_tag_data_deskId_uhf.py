"""
This is a sample file for the metratec deskid uhf with the metratec rfid sdk.

The program uses the connected deskid uhf reader on the serial port /dev/ttyUSB.

After connecting, write an access password to the tag and lock the access password and the tag data
"""

import asyncio
from metratec_rfid import DeskIdUhf
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
        access_password = "ABCD1234"
        lock_mode = 2  # writable only in secured state

        # set reader access password - only if the tag has already a access password
        # await reader.set_access_password("ABCD1234")

        # write tag access password to one tag
        response = await reader.write_tag_access_password(access_password, True)
        if len(response['transponders']) == 1:
            tag = response['transponders'][0]
            print(f'Access password written to tag {tag.get_epc()}')
        else:
            if len(response['errors']) == 1:
                tag = response['errors'][0]
                print(f"{tag.get_epc()}: Access password write error: {tag.get_error_message()}")
            else:
                print("No tag found to write access password")
                return

        # set reader access password
        await reader.set_access_password("ABCD1234")

        # lock tag access password - mode 2 means the epc is only writeable in the secured state
        response = await reader.lock_tag_access_password(lock_mode, True)
        if len(response['transponders']) == 1:
            tag = response['transponders'][0]
            print(f'Access password locked to tag {tag.get_epc()}')
        else:
            if len(response['errors']) == 1:
                tag = response['errors'][0]
                print(f"{tag.get_epc()}: Access password lock error: {tag.get_error_message()}")
            else:
                print("No tag found to lock access password")
                return

        # lock tag access password - mode 2 means the epc is only writeable in the secured state
        response = await reader.lock_tag_data(lock_mode, True)
        if len(response['transponders']) == 1:
            tag = response['transponders'][0]
            print(f'Tag data locked to tag {tag.get_epc()}')
        else:
            if len(response['errors']) == 1:
                tag = response['errors'][0]
                print(f"{tag.get_epc()}: Tag data lock error: {tag.get_error_message()}")
            else:
                print("No tag found to lock data")
                return

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
