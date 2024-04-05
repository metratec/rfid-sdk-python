.. _tutorials:

Tutorials
=========

This section provides tutorials for various parts of the library

Continuous Inventory
####################

If you want to set the reader in a continuous scanning mode, then you can start the inventory scan
with the method "start_inventory". To stop the scan, call the "stop_inventory" method. The transponders found
can be fetched with the method "fetch_inventory".

Here an code example ::

  async def main():
    
    reader = DeskIdIso("Reader01", "COM1")
    await reader.connect();
    await reader.start_inventory()
    end_time = time.time() + 60.0
    while end_time > time.time():
      await asyncio.sleep(2.0)
      inv = await reader.fetch_inventory()
      print(f"Read Tags: {inv}")
    await reader.stop_inventory()
    await reader.disconnect();

  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())

If you do not want to fetch the inventory yourself, you can register an inventory callback
that will be invoked when new transponders are found. See section `Inventory events`_


Event handling
##############

Status events
-------------

The reader classes can trigger events when a connection is changed. 
To subscribe to the events, the callback for the status can be set. 
The callback parameter is a status dictionary which contains
  * the 'status' as an integer. (-1 means not connected, 1 and above means connected)
  * the 'message' which is a readable status description
  * the change 'timestamp'  
  
Here an code example ::

  def reader_status_changed(status):
    print(f"The status from Reader {status['instance']} has changed to {status['message']}")

  async def main():
    
    reader = DeskIdIso("Reader01", "COM1")
    reader.set_cb_status(reader_status_changed)
    
    await reader.connect();
    await asyncio.sleep(1.0);
    await reader.disconnect();

  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())

Inventory events
----------------

When an inventory request is sent or the inventory query is started,
the found transponders are reported via an event. 

To subscribe to the events, set the callback for the inventory with the
'set_cb_inventory' method. The callback parameter is a list of transponders.

Here an code example ::

  def new_inventory(inventory):
    for tag in inventory:
      print(f"Tag found: {tag.get_id()")

  reader = DeskIdIso("Reader01", "Com1")
  reader.set_cb_inventory(new_inventory)
  
  async def main():
    await reader.connect();
    await reader.start_inventory();
    await asyncio.sleep(5.0);
    await reader.stop_inventory();
    await reader.disconnect();

  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())