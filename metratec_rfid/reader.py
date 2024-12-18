"""
metratec rfid reader base class
"""

from abc import abstractmethod
import asyncio
from time import time
from typing import Any, Callable, Dict, List, Optional
from serial.tools import list_ports

from .tag import Tag
from .status_class import BaseClass
from .reader_exception import RfidReaderException
from .connection.connection import Connection
from .connection.serial_connection import SerialConnection

# disable 'Too many lines in module' warning - pylint: disable=C0302


class ExpectedReaderInfo():
    """Expected reader info decorator
    """
    # disable Too few public methods warning - pylint: disable=R0903

    def __init__(self, firmware_name: str, hardware_name: str, min_firmware: float) -> None:
        """_summary_

        Args:
            firmware_name (str): firmware name
            hardware_name (str): hardware name
            min_firmware (str): minimum required firmware version
        """
        self._firmware_name = firmware_name
        self._hardware_name = hardware_name
        self._min_firmware = min_firmware

    def __call__(self, clazz):
        """
        Adds the property to the class properties field.
        Creates the field if needed.

        :param clazz: The class to decorate
        :return: The decorated class
        """
        properties = getattr(clazz, "_expected_reader", None)
        if not properties:
            properties = {}
            setattr(clazz, "_expected_reader", properties)
        properties["firmware_name"] = self._firmware_name
        properties["hardware_name"] = self._hardware_name
        properties["min_firmware"] = self._min_firmware
        return clazz


class RfidReader(BaseClass):
    """The base implementation of a rfid reader
    """

    # disable 'Too many public methods' warning - pylint: disable=R0904
    # disable 'Too many instance attributes warning' - pylint: disable=R0902

    RUNNING = 1
    BUSY = 0
    ERROR = -1
    WARNING = -2

    def __init__(self, connection: Connection, instance: str = "") -> None:
        super().__init__(instance)
        self._connection: Connection = connection
        self._connection.set_cb_connection_made(self._connection_made)
        self._connection.set_cb_connection_lost(self._connection_lost)
        self._connection.set_cb_data_received(self._connection_data_received)
        self._cb_input_changed: Optional[Callable[[int, bool], None]] = None
        self._cb_inventory: Optional[Callable[[List[Tag]], None]] = None
        self._task_config: Optional[asyncio.Task] = None
        self._task_connection_check: Optional[asyncio.Task] = None
        self._handle_data: Callable = self._data_received_config
        self._send: Callable = self._send_not_connected
        self._config: dict = {}
        self._receiver_buffer: asyncio.Queue = asyncio.Queue()
        self._inventory: Dict[str, Tag] = {}
        self._inventory_condition = asyncio.Condition()
        self._fire_empty_inventories = False
        self._heartbeat: int = 10
        self._timeout: float = 25.0
        self._last_message_time: float = 0

    async def connect(self, timeout: float = 5.0, port_re: str = "USB") -> None:
        """Connect the reader.

        If no port is set during initialization, it will be determined automatically.
        For this, `port_re` will be used to filter potential serial ports.

        Args:
            timeout (float, optional): Maximum waiting time for the connection.
                Defaults to 5.0 seconds.
            port_re (str, optional): Regular expression for finding serial ports automatically.
                Defaults to "USB".

        Raises:
            RfidReaderException: Reader error or connection timeout.
        """
        if self._connection.is_connected():
            self._update_status(self.BUSY, "configuring")
            self._send = lambda data: self._connection.send(data.encode())
            self._handle_data = self._data_received_config
            self._task_config = asyncio.ensure_future(self._config_device())
            await self._connect(timeout=timeout)
        elif isinstance(self._connection, SerialConnection):
            port = self._connection.get_port()
            if port:
                port_list = [port]
            else:
                port_list = []
                for p in list_ports.grep(port_re):
                    port_list.append(p.device)

            if len(port_list) == 0:
                raise RfidReaderException("No connection port set or found automatically")

            for port in port_list:
                try:
                    self._connection.set_port(port)
                    await self._connect(timeout=timeout)
                    self.get_logger().info("Connection attempt on port %s successful.", port)
                    return
                except RfidReaderException as e:
                    self.get_logger().error("Connection attempt on port %s failed: %s", port, e)
                    self._connection.disconnect()

            raise RfidReaderException("Serial connection failed")
        else:
            # assuming socket connection is the only alternative
            address = self._connection.get_info().split(":")[0]
            if not address:
                # FIXME find reader via avahi/zeroconf
                raise NotImplementedError("Auto-IP not available")
            await self._connect(timeout=timeout)

    async def _connect(self, timeout: float = 5.0) -> None:
        if not self._connection.is_connected():
            self._handle_data = self._data_received_config
            self._connection.connect()
        max_time: float = time() + timeout
        while True:
            await asyncio.sleep(0.02)
            if self.is_running():
                return
            if self.get_status()['status'] < 0:
                raise RfidReaderException(self.get_status()['message'])
            if max_time <= time():
                self._connection.disconnect()
                self._send = self._send_not_connected
                raise RfidReaderException("Connection timeout")

    async def disconnect(self) -> None:
        """Disconnect the reader.
        """
        # stop continuous inventories:
        if self._connection.is_connected():
            try:
                await self.stop_inventory()
            except RfidReaderException:
                # ignore reader exceptions
                pass
        self._stop_internal_tasks()
        self._connection.disconnect()
        self._inventory.clear()
        self._send = self._send_not_connected

    def is_connected(self) -> bool:
        """Return whether the reader is connected.

        Returns:
            bool: True if connected.
        """
        return self._connection.is_connected()

    def is_running(self) -> bool:
        """Return whether the reader is running.

        Returns:
            bool: True if the reader is running correctly.
        """
        return self._status['status'] == self.RUNNING

    def set_cb_inventory(self, callback: Optional[Callable]) -> Optional[Callable]:
        """
        Set the callback for a new inventory. The callback has the following arguments:
        * tags (List[Tag]) - the tags

        Returns:
            Optional[Callable]: the old callback
        """
        old = self._cb_inventory
        self._cb_inventory = callback
        return old

    # FIXME move to IO?
    def set_cb_input_changed(self, callback: Optional[Callable]) -> Optional[Callable]:
        """Set the callback for the input-changed event.

        Define a callback which will be triggered whenever an input pin
        changes its value. The callback has the following arguments:

        * pin (int) - The changed pin number.
        * value (boolean) - The pin state.

        Use `enable_input_events()` to activate.

        Args:
            callback (Callable): Reference to the callback function to use.

        Returns:
            Optional[Callable]: The old callback.

        Example:
            >>> def my_callback(pin, value)
            >>>     pass
            >>> set_cb_input_changed(my_callback)
            >>> enable_input_events()
        """
        old = self._cb_input_changed
        self._cb_input_changed = callback
        if self.get_status()['status'] == self.RUNNING:
            asyncio.ensure_future(self._enable_input_events(self._cb_input_changed is not None))
        return old

    def enable_fire_empty_inventory(self, enable: bool):
        """En-/disable callbacks for empty inventories.

        By default, the event handler for inventories, which can be defined
        with `set_cb_inventory()`, is not called when an inventory was
        technically successful but no tags have been found.
        If this is set to `True`, empty inventories will also trigger
        the defined callback.

        Args:
            enable (bool): Set to True, to enable empty inventory events.
        """
        self._fire_empty_inventories = enable

    async def fetch_inventory(self, wait_for_tags: bool = False) -> List[Tag]:
        """
        Can be called when an inventory has been started. Waits until at least one tag is found
        and returns all currently scanned transponders from a continuous scan.

        Args:
            wait_for_tags (bool): Set to true, to wait until transponders are available.

        Returns:
            List[Tag]: A list with the transponders found.
        """
        async with self._inventory_condition:
            if wait_for_tags:
                if not self._inventory:
                    await self._inventory_condition.wait()
            inventory = list(self._inventory.values())
            self._inventory.clear()
            return inventory

    async def set_heartbeat(self, interval: int) -> None:
        """Set the heartbeat interval of the reader.

        If the interval is larger than 0, the SDK will regularly check
        whether the reader is still connected and automatically
        attempt to re-connect and raise and error on failure.

        Args:
            interval (float): Interval in seconds [0, 60].
        """
        self._heartbeat = interval
        if self.is_connected():
            self._timeout = 2.5 * self._heartbeat

    def get_status(self) -> Dict[str, Any]:
        """Return status information about the reader.

        The status information dictionary contains the following keys:

        * instance (str): Name of the reader.
        * status (int): Reader status enum (RUNNING = 1, BUSY = 0,
          ERROR = -1, WARNING = -2).
        * message (str): Status message.
        * timestamp (float): Timestamp of the last status change.

        Returns:
            Dict[str, Any]: Dictionary with status information.
        """
        return self._status

    ###############################################################################################
    # Abstract methods
    ###############################################################################################

    @abstractmethod
    async def send_custom_command(self, command: str) -> List[str]:
        """Send a command to the reader and return the response

        Args:
            command (str): the command

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[str]: The reader responses. In case of an set command the list is empty
        """

    # FIXME move to IO?
    @abstractmethod
    async def enable_input_events(self, enable: bool = True) -> None:
        """En-/disable the reader input events.

        Whenever the state of an input pin changes, the event handler
        defined with `set_cb_input_changed()` will be triggered.

        Args:
            enable (bool, optional): True to enable. Defaults to True.

        Raises:
            RfidReaderException: If a reader error occurs.
        """

    @abstractmethod
    async def get_reader_info(self) -> Dict[str, Any]:
        """Return hard- and software information of the reader.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with 'firmware', 'firmware_version',
            'hardware', 'hardware_version' and 'serial_number' keys.
        """

    @abstractmethod
    async def set_antenna(self, antenna: int) -> None:
        """Set the antenna port to be used.

        Args:
            antenna (int): The antenna port to be used.

        Raises:
            RfidReaderException: If a reader error occurs.
        """

    @abstractmethod
    async def get_antenna(self) -> int:
        """Return the currently used antenna port.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            int: The currently used antenna port.
        """

    @abstractmethod
    async def get_inventory(self):
        """Get an inventory from the current antenna.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[Tag]: An array with the transponders found.
        """

    @abstractmethod
    async def start_inventory(self) -> None:
        """Start a continuous inventory.

        This will cause the reader to perform inventories continuously
        until the `stop_inventory()` function is called.

        Raises:
            RfidReaderException: If a reader error occurs.
        """

    @abstractmethod
    async def stop_inventory(self) -> None:
        """Stop the continuous inventory.

        Raises:
            RfidReaderException: If a reader error occurs.
        """

    ###############################################################################################
    # Abstract internal methods
    ###############################################################################################

    @abstractmethod
    async def _prepare_reader_communication(self) -> None:
        """Override for prepare the reader for the communication.
        Called before the config reader method
        """

    @abstractmethod
    async def _config_reader(self) -> None:
        """Override for configure and initialise the reader"""

    @abstractmethod
    def _data_received_config(self, data: str, timestamp: float):
        """
        Called from the connection instance, to handle the received data - UNTIL THE READER IS CONFIGURED

        Args:
            data (str): the received data
            timestamp (float): the timestamp
        """

    @abstractmethod
    def _data_received(self, data: str, timestamp: float):
        """Called from the connection instance, to handle the received data

        Args:
            data (str): the received data
            timestamp (float): the timestamp
        """

    ###############################################################################################
    # Internal methods
    ###############################################################################################

    def _connection_made(self) -> None:
        self._update_status(self.BUSY, "configuring")
        self._send = lambda data: self._connection.send(data.encode())
        self._task_config = asyncio.ensure_future(self._config_device())

    def _connection_lost(self, reason) -> None:
        self._stop_internal_tasks()
        self._send = self._send_not_connected
        if self._status['status'] != self.ERROR:
            self._update_status(self.ERROR, reason)

    async def _check_connection(self) -> None:
        """Check the connection - reconnect the device if no messages have been received for a while
        """
        if self._heartbeat <= 0:
            return
        self._timeout = 2.5 * self._heartbeat
        while self.get_status()['status'] >= 1:
            await asyncio.sleep(5)
            if self._last_message_time + self._timeout >= time():
                continue
            # connection lost
            self._update_status(self.ERROR, 'connection lost')
            try:
                # await self.disconnect()
                self._connection.disconnect()
                self._send = self._send_not_connected
                await self.connect()
            except TimeoutError:
                pass
            break

    def _add_data_to_receive_buffer(self, data: str) -> None:
        """ add the received data to the internal response buffer """
        self._receiver_buffer.put_nowait(data)

    async def _recv(self, timeout: float = 2.0) -> str:
        """Returns the next answer in the buffer or None if it is empty and the timeout has been reached

        Args:
            timeout (float, optional): The response timeout. Defaults to 2.0.

        Raises:
            TimeoutError: if the timeout is reached

        Returns:
            str: the received response
        """
        response: List[str] = []
        try:
            await asyncio.wait_for(self._get(response), timeout=timeout)
            return response[0]
        except Exception as err:
            raise TimeoutError("response timeout") from err

    async def _get(self, response: List[str]) -> None:
        # Adds a received reader response to the passed array
        try:
            response.append(await self._receiver_buffer.get())
        except asyncio.CancelledError:
            # expected - tow exception are thrown - CancelledError here and a TimeoutError in "asyncio.wait_for"
            pass

    def _clear_response_buffer(self) -> None:
        """ Clear the response buffer before a new command is send"""
        for _ in range(self._receiver_buffer.qsize()):
            self.get_logger().info("Unexpected reader response in buffer: %s", self._receiver_buffer.get_nowait())

    async def _config_device(self) -> None:
        """Configure the reader"""
        try:
            await self._prepare_reader_communication()
            await self._config_reader()
            try:
                self._heartbeat = self._config.get('heartbeat', self._heartbeat)
                await self.set_heartbeat(self._heartbeat)
            except RfidReaderException:
                self.get_logger().debug("no heartbeat available - connection check is disabled")
                self._heartbeat = 0
            try:
                await self.enable_input_events(self._cb_input_changed is not None)
            except RfidReaderException as err:
                if "not available" not in str(err):
                    raise err
            self._update_status(self.RUNNING, "running")
            self._task_connection_check = asyncio.ensure_future(self._check_connection())
            self._handle_data = self._data_received
        except (TimeoutError, RfidReaderException) as err:
            msg: str = f"Configuration Error - {err}" if isinstance(err, RfidReader) else str(err)
            self.get_logger().warning(msg)
            self._update_status(self.ERROR, msg)
            # try reconfigure after 5 seconds
            await asyncio.sleep(5)
            self._task_config = asyncio.ensure_future(self._config_device())

    def _send_not_connected(self, data: str) -> None:
        raise RfidReaderException("Not connected")

    def _connection_data_received(self, data: bytes) -> None:
        timestamp: float = time()
        self._last_message_time = timestamp
        self._handle_data(data.decode(), timestamp)

    def _stop_internal_tasks(self) -> None:
        if self._task_connection_check and not self._task_connection_check.done():
            self._task_connection_check.cancel()
        if self._task_config and not self._task_config.done():
            self._task_config.cancel()

    async def _enable_input_events(self, enable: bool = True):
        try:
            await self.enable_input_events(enable)
        except RfidReaderException as err:
            self.get_logger().warning("Error enable input events - %s", err)

    def _fire_inventory_event(self, inventory: List[Tag], continuous: bool = True) -> None:
        """ Checks the inventory and calls the inventory callback """
        if not self._cb_inventory:
            if inventory and continuous:
                asyncio.create_task(self._update_inventory(inventory))
            return
        if not self._fire_empty_inventories and not inventory:
            return
        self._cb_inventory(inventory)

    def _fire_input_changed_event(self, pin: int, new_value: bool) -> None:
        if not self._cb_input_changed:
            return
        self._cb_input_changed(pin, new_value)

    async def _update_inventory(self, inventory: List[Tag]):
        async with self._inventory_condition:
            for tag in inventory:
                if tag.get_id() in self._inventory:
                    current_tag: Tag = self._inventory[tag.get_id()]
                    current_tag.set_seen_count(current_tag.get_seen_count()+tag.get_seen_count())
                    current_tag.set_last_seen(tag.get_last_seen())
                else:
                    self._inventory[tag.get_id()] = tag
            self._inventory_condition.notify()
