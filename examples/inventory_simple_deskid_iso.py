import asyncio
from metratec_rfid import DeskIdIso


async def print_inventory(serial_port: str):

    deskid = DeskIdIso("reader01", serial_port)
    await deskid.connect()
    print(await deskid.get_inventory())
    await deskid.disconnect()


loop = asyncio.new_event_loop()
loop.run_until_complete(print_inventory("/dev/ttyUSB0"))
