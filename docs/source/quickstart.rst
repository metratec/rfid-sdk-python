.. _quickstart:

Quick-start
###########

Connect a reader and read a transponder
=======================================

::

  import asyncio
  from metratec_rfid import DeskIdIso


  async def print_inventory(serial_port: str):

      deskid = DeskIdIso(instance="reader01", serial_port=serial_port)
      await deskid.connect()
      print(await deskid.get_inventory())
      await deskid.disconnect()


  loop = asyncio.new_event_loop()
  loop.run_until_complete(print_inventory("/dev/ttyUSB0"))



Using of the status and inventory callback
==========================================

::

  import asyncio

  from metratec_rfid import PulsarMX
  from metratec_rfid import RfidReaderException
  
  
  async def main():
  
      # Create an instance and define the serial connection
      reader = PulsarMX(instance="Reader", hostname="192.168.2.239")
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