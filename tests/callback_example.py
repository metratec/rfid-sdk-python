"""
This is a sample file for the metratec deskid uhf with the metratec rfid sdk.

The program uses the connected deskid uhf reader on the serial port /dev/ttyUSB.

After connecting, the epc of the current transponder is overwritten.

"""
# disable 'docstring' warning - pylint: disable=C0114,C0115,C0116
# disable 'wrong-import-position' warning - pylint: disable=C0413
# disable 'Raising too general exception' warning - pylint: disable=W0719

import asyncio
import sys
import os
sys.path.append(os.getcwd())
from metratec_rfid.pulsar_mx import PulsarMX  # noqa -- flake ignore
from metratec_rfid.reader_exception import RfidReaderException  # noqa -- flake ignore


async def main():
    """Callback example"""

    # Create an instance and define the serial connection
    reader = PulsarMX(instance="Reader", hostname="192.168.2.203")
    # set a callback for the reader status
    reader.set_cb_status(lambda status: print(f"status changed: {status}"))
    # set a callback for the inventories
    reader.set_cb_inventory(lambda inventory: print(f"new inventory: {inventory}"))

    # connect the reader
    try:
        await reader.connect()
        # set the reader power
        await reader.set_power(17)
        # start the inventory
        await reader.set_heartbeat(2)
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
