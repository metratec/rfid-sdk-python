.. _quickstart:

Quickstart
##########

The main part of the library are the reader objects.
The following code snippets use one of the readers as an example.
You have to use the class that matches your device.

The :ref:`api` section contains detailed information about each reader.

- UHF ASCII reader (legacy): :ref:`DeskIdUhf<DeskIdUhf>`, :ref:`PulsarMX<PulsarMX>`
- HF ASCII reader (legacy): :ref:`DeskIdIso<DeskIdIso>`, :ref:`QuasarLR<QuasarLR>`,
  :ref:`QuasarMX<QuasarMX>`
- UHF AT reader: :ref:`PulsarLR<PulsarLR>`, :ref:`Plrm<Plrm>`, 
  :ref:`DeskIdUhfv2<DeskIdUhfv2>`, :ref:`DeskIdUhfv2FCC<DeskIdUhfv2FCC>`,
  :ref:`ORG2<QRG2>`, :ref:`QRG2FCC<QRG2FCC>`, :ref:`DwarfG2v2<DwarfG2v2>`,
  :ref:`DwarfG2Miniv2<DwarfG2Miniv2>`, :ref:`DwarfG2XRv2<DwarfG2XRv2>`
- NFC AT reader: :ref:`DeskIdNfc<DeskIdNfc>`, :ref:`QrNfc<QrNfc>`


Minimal inventory example
=========================

This is a minimal example that shows reader object initialization,
runs a single inventory and prints the result.

Attention! You have to adapt the reader class to match your conditions.

::

    import asyncio
    from metratec_rfid import RfidReaderException
    # Attention! Change the reader class to match your device.
    from metratec_rfid import DeskIdUhfv2


    async def print_inventory(reader):
        """Connect the reader, run a single inventory and print the result.
        """
        try:
            await reader.connect()
            print(await reader.get_inventory())
            await reader.disconnect()
        except RfidReaderException as e:
            print(e)


    # Create a new reader object and run the example function.
    # Attention! Change the serial port according to your PC.
    SERIAL_PORT = "COM41"  # "/dev/ttyUSB0"
    # Attention! Change the reader class to match your device.
    reader01 = DeskIdUhfv2("reader01", SERIAL_PORT)
    asyncio.run(print_inventory(reader01))


Using automatic reader detection 
================================

The SDK's utility function `detect_readers()` can be used to automatically
find all readers connected to the system (via USB) and return the appropriate
reader class object.

::

    import asyncio
    from metratec_rfid import RfidReaderException
    from metratec_rfid import detect_readers


    async def print_inventory():
        """Find connected readers, run a single inventory on each and print the result.
        """
        readers = await detect_readers()
        for port, reader in readers.items():
            print(f"Running example with {reader.__class__.__name__} on port {port}")
            try:
                await reader.connect()
                print(await reader.get_inventory())
                await reader.disconnect()
            except RfidReaderException as e:
                print(e)


    # Run the example function on every reader connected to the system.
    asyncio.run(print_inventory())