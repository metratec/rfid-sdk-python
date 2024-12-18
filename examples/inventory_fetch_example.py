"""
This is a sample file for fetching results of a continuous inventory scan.

The program uses the get_reader() example utility to init a new reader
object from commandline arguments.

After connecting, a continuous inventory is started which will run for a
few seconds. A background task will collect all the results which are
fetched and printed in regular intervals.
"""

import asyncio
import time

from example_utils import get_reader
from metratec_rfid import RfidReaderException


async def main():
    """Run the inventory fetch example.
    """
    # Create a reader instance from commandline arguments.
    reader = get_reader()
    # Set a callback for reader status changes.
    reader.set_cb_status(lambda status: print(f"Status changed: {status}"))

    try:
        # Connect the reader.
        await reader.connect()
        # Start a continuous inventory.
        # The results will be stored by another task.
        await reader.start_inventory()
        # Let the inventory run for 10 seconds and query results every 2s.
        end_time = time.time() + 10.0
        while end_time > time.time():
            # Let the main task wait while continuous inventory is running.
            await asyncio.sleep(2.0)
            # Fetch and print new inventory data.
            inv = await reader.fetch_inventory()
            print(f"New inventory: {inv}")
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
