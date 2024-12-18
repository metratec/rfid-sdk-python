.. _tutorials:

Tutorials
#########

This section provides tutorials for various parts of the library.

Transponder/Tag Classes 
=======================

Reader functions that operate on tags usually return a list of 
:ref:`Tag<transponder>` objects.
These objects contain all available data of each individual transponder
and information about the command execution.

Continuous Inventory
====================

As shown in the :ref:`Minimal Example<quickstart>`, you can perform a single
inventory scan with `get_inventory()`.
If you want to set the reader into a continuous scanning mode instead,
you can use `start_inventory()` method.
To stop the scan, call the `stop_inventory()` method.

The inventory results are collected by a background task and the transponders
that have been found can be fetched with `fetch_inventory()`.

Here is a code example:

::

    async def main():
        # Create a reader instance and connect.
        reader = DeskIdIso("reader01", "COM1")
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
        # Stop the continuous inventory operation and shut down.
        await reader.stop_inventory()
        await reader.disconnect()

    asyncio.run(main())


If you do not want to fetch the inventory yourself, you can register an
inventory callback that will be invoked when new transponders are found.
See section `Inventory Events`_.


Event Handling
==============

Status Events
-------------

The reader class can trigger events when its internal status changes,
for example after a call to `connect()`. 
To subscribe to the events, a callback for the status must be set. 
The callback parameter is a status dictionary which contains the following keys.

* instance (str): Name of the reader.
* status (int): Reader status enum (RUNNING = 1, BUSY = 0,
  ERROR = -1, WARNING = -2).
* message (str): Status message.
* timestamp (float): Timestamp of the last status change.

Here is a code example:

::

    def reader_status_changed(status):
        print(f"The status of Reader {status['instance']} has changed to {status['message']}")

    async def main():
        reader = DeskIdIso("reader01", "COM1")
        reader.set_cb_status(reader_status_changed)
    
        await reader.connect()
        await asyncio.sleep(1.0)
        await reader.disconnect()

    asyncio.run(main())

Alternatively, you can query the reader status at any point with its
`get_status()` method.

Inventory Events
----------------

Whenever a new inventory result is available, the transponders that have 
been found are reported via an event.

To subscribe to the events, set the callback for inventories with the
`set_cb_inventory()` method. The callback parameter is a list of transponders.

Here is a code example:

::

    def new_inventory(inventory):
        for tag in inventory:
            print(f"Tag found: {tag.get_id()")

    async def main():
        reader = DeskIdIso("reader01", "/dev/serial0")
        reader.set_cb_inventory(new_inventory)

        await reader.connect()
        await reader.start_inventory()
        await asyncio.sleep(5.0)
        await reader.stop_inventory()
        await reader.disconnect()

    asyncio.run(main())

Input Events
------------

Some readers, such as the PulsarLR, have physical input pins.
To be notified about state changes, set a callback and enable input events.

::

    def input_changed(pin: int, value: bool):
        print(f"Pin {pin} changed to {value}")

    async def main():
        reader = PulsarLR("reader01", "192.168.2.153")
        reader.set_cb_input_changed(input_changed)
        await reader.connect()
        await reader.enable_input_events(True)
        # ...

    asyncio.run(main())

Pin states can also be queried on demand with the `get_input()` method.

Error Handling
==============

Most reader methods raise the libraries `RfidReaderException` if an
error occurs. 
Therefore it is recommended wrap calls to reader functions in a
try-except block to handle any errors.

::

    try:
        await reader.get_inventory()
    except RfidReaderException as err:
        print(f"Reader exception: {err}")

Reader Settings
===============

The readers can be configured in various ways.
Especially the UHF readers offer a lot of customization options.
The available methods and options vary a lot between different devices.
Again, reference the :ref:`API` for details. 

Here are some example functions that the reader class provide:

::

    # Set the power level for inventories and other RF operations.
    reader.set_power(750)  # mW for legacy HF readers
    reader.set_power(12)  # dBm for others

    # Only readers with multiple antenna ports support switching antennas.
    reader.set_antenna(2)

    # This will cause tags to only respond once during an inventory run.
    reader.set_inventory_settings(only_new_tags=True)

    # UHF readers can automatically filter tag populations by masking.
    reader.set_mask("ABCD0123", memory="EPC")

Read/Write Tag Data
===================

UHF Reader
----------

There are many functions to read and write various data of a transponder.
Take a look at the :ref:`API` section for a complete list.
Similar to inventories, these functions return a list of tag objects that
contain different information about the transponder, depending on
the executed command.

For instance, here is an example that reads the first 4 bytes of the
tag ID and prints it on success.

::
  
    response: List[UhfTag] = await reader.read_tag_tid(start=0, length=4)
  
    for tag in response:
        if tag.has_error():
            print(f'EPC: {tag.get_epc()}, Error: {tag.get_error_message()}')
        else:
            print(f'EPC: {tag.get_epc()}, TID: {tag.get_tid()}')

The `write_tag_epc()` method allows you to change a transponders EPC.
The transponder to modify is specified by its tag ID in order to ensure
that only the correct tag is changed, should more than one tag be in range.

::
    
    tag_id = "E2804704"
    new_epc = "12345678"
    response = await reader.write_tag_epc(tag_id, new_epc)

    for tag in response:
        if tag.has_error():
            print(f'EPC: {tag.get_epc()}, Error: {tag.get_error_message()}')
        else:
            print(f'EPC: {tag.get_epc()}, Success')

HF Reader
---------

HF readers use slightly different methods to read and write data.
Here are examples for reading tag data with different HF readers.
Look at the :ref:`API` section for details about each reader.

Legacy readers (e.g. :ref:`DeskID ISO<DeskIdIso>`, :ref:`QuasarLR<QuasarLR>`
and :ref:`QuasarMX<QuasarMX>`) use the `read_tag_data()` function to read
individual blocks of data.

::
    
    block_number = 1
    reader.read_tag_data(block_number)

Newer NFC readers (e.g. :ref:`DeskID NFC<DeskIdNfc>` and :ref:`QR-NFC<QrNfc>`)
use the `read_data()` function instead and allow you to read multiple
blocks at once.

::

    start_block = 1
    reader.read_data(start_block, number_of_blocks=1)


Complete Example (UHF Reader)
=============================

Here is a complete code example that implements many of the reader
features at once.

::

    import asyncio

    from metratec_rfid import PulsarLR
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
        # Create an instance and define the connection.
        reader = PulsarLR(instance="Reader", hostname="192.168.2.239")
        # Set a callback for reader status changes.
        reader.set_cb_status(lambda status: print(f"Status changed: {status}"))
        # Set a callback for new inventories.
        reader.set_cb_inventory(print_tags))
  
        try:
            # Connect the reader.
            await reader.connect()
            # Modify the output power.
            await reader.set_power(17)
            # Start a continuous inventory for 10 seconds.
            await reader.start_inventory()
            await asyncio.sleep(10)
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