"""
This is a sample file for using the inventory callback method of the library.

The program uses the get_reader() example utility to init a new reader
object from commandline arguments.

After connecting, a continuous inventory is started which will run for a
few seconds. Whenever new tag data is available, it is printed to the console.
"""

import asyncio

from example_utils import get_reader
from metratec_rfid import RfidReaderException


def print_tags(tag_list):
    """
    Inventories return a list of Tag objects.
    This function prints each individual tag to the console.
    """
    print("New inventory:")
    for tag in tag_list:
        print(tag)


async def main():
    """Run the inventory callback example.
    """
    # Create a reader instance from commandline arguments.
    reader = get_reader()
    # Set a callback for reader status changes.
    reader.set_cb_status(lambda status: print(f"Status changed: {status}"))
    # Set a callback for new inventories.
    reader.set_cb_inventory(print_tags)

    try:
        # Connect the reader.
        await reader.connect()
        # Start a continuous inventory. The results will be parsed in
        # another task and the callback defined with set_cb_inventory()
        # will be triggered whenever new data is available.
        await reader.start_inventory()
        # Let the main task wait while continuous inventory is running.
        await asyncio.sleep(10)
        # Stop the continuous inventory operation.
        await reader.stop_inventory()
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
