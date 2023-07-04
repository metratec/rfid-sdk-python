""" tunnel implementation """

import asyncio
from time import time
from typing import Any, Callable, Dict, List, Optional

from .status_class import BaseClass
from .reader_exception import RfidReaderException

from .tag import Tag

from .reader import RfidReader


class Tunnel(BaseClass):
    """ Tunnel implementation

    Starting if the front input is triggered.

    Stopping if the back input is triggered and has his old value.

    """
    # disable 'Too many instance attributes warning' - pylint: disable=R0902
    RUNNING = 1
    BUSY = 0
    ERROR = -1

    def __init__(self, reader: RfidReader, instance: str = "") -> None:
        super().__init__(instance)
        self._reader: RfidReader = reader
        self._is_started: bool = False
        self._cb_scan_finished: Optional[Callable] = None
        self._reader_org_values: Dict[str, Any] = {}
        self._start_input: int = 1
        self._start_trigger_on_high: bool = True
        self._start_delay: float = 0.0
        self._stop_input: int = 2
        self._stop_trigger_on_high: bool = False
        self._stop_delay: float = 0.0
        self._current_scan: Dict[str, Any] = {}
        self._last_scan: Dict[str, Any] = {'type': "scan", 'id': 0, 'start_time': 0.0, 'stop_time': 0.0}

    def set_cb_scan(self, callback: Optional[Callable]) -> Optional[Callable]:
        """
        Set the callback for a new inventory. The callback has the following arguments:
        * tags (Dict[str, Any]) - the scan, contains: ['id', 'start_time', 'stop_time', 'inventory']

        Returns:
            Optional[Callable]: the old callback
        """
        old = self._cb_scan_finished
        self._cb_scan_finished = callback
        return old

    def set_input_start(self, start_pin: int, trigger_value: str = "HIGH", start_delay: float = 0) -> None:
        """Configure the start trigger

        Args:
            start_pin (int): reader input pin
            trigger_value (str, optional): trigger on "HIGH" or "LOW". Defaults to "HIGH"
            start_delay (float, optional): Starting delay. Defaults to 0.
        """
        self._start_input = start_pin
        self._start_trigger_on_high = "HIGH" in trigger_value.upper()
        self._start_delay = start_delay

    def set_input_stop(self, stop_pin: int, trigger_value: str = "HIGH", start_delay: float = 0) -> None:
        """Configure the stop trigger

        Args:
            stop_pin (int): reader input pin
            trigger_value (str, optional): trigger on "HIGH" or "LOW". Defaults to "HIGH"
            start_delay (float, optional): Starting delay. Defaults to 0.
        """
        self._stop_input = stop_pin
        self._stop_trigger_on_high = "HIGH" in trigger_value.upper()
        self._stop_delay = start_delay

    def get_config(self) -> Dict[str, Any]:
        """"Returns the tunnel configuration

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict[str, Any]: the tunnel configuration
        """
        config: Dict[str, Any] = {}
        config['start_input'] = self._start_input
        config['start_trigger_value'] = self._start_trigger_on_high
        config['start_delay'] = self._start_delay
        config['stop_input'] = self._stop_input
        config['stop_trigger_value'] = self._stop_trigger_on_high
        config['stop_delay'] = self._stop_delay
        return config

    def set_config(self, config: Dict[str, Any]) -> None:
        """set the tunnel configuration - see get_config()

        Args:
            config (Dict[str, Any]): tunnel configuration
        """
        if not config or not isinstance(config, dict):
            return
        start_input: Any = config.get('start_input')
        if isinstance(start_input, int):
            self._start_input = start_input
        start_trigger_value: Any = config.get('start_trigger_value')
        if isinstance(start_trigger_value, str):
            self._start_trigger_on_high = "HIGH" in start_trigger_value.upper()
        start_delay: Any = config.get('start_delay')
        if isinstance(start_delay, float):
            self._start_delay = start_delay

        stop_input: Any = config.get('stop_input')
        if isinstance(stop_input, int):
            self._stop_input = stop_input
        stop_trigger_value: Any = config.get('stop_trigger_value')
        if isinstance(stop_trigger_value, str):
            self._stop_trigger_on_high = "HIGH" in stop_trigger_value.upper()
        stop_delay: Any = config.get('stop_delay')
        if isinstance(stop_delay, float):
            self._stop_delay = stop_delay

    async def set_reader_config(self, config: Dict[str, Any]) -> None:
        """Writes the config to the reader. To config must have the same structure like the response
        from the get_config method.

        Args:
            config (Dict[str, Any]): configuration dictionary

        Raises:
            RfidReaderException: if an reader error occurs
        """
        # await self._reader.set_config(config)
        # Todo add reader config

    async def get_reader_config(self) -> Dict[str, Any]:
        """Returns the reader configuration

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict[str, Any]: the reader configuration
        """
        # return await self._reader.get_config()
        # Todo add reader config
        return {}

    async def start(self) -> None:
        """Start the tunnel functionality

        Raises:
            TimeoutError: if the reader can not be connected
        """
        if self._is_started:
            return
        self._reader_org_values['connected'] = self._reader.is_connected()
        if not self._reader.is_connected():
            await self._reader.connect()
        self._is_started = True
        # set the necessary callback and store the current callbacks
        self._reader_org_values['cb_input_changed'] = self._reader.set_cb_input_changed(self._input_changed)
        self._reader_org_values['cb_status'] = self._reader.set_cb_status(self._reader_status_changed)
        self._reader_org_values['cb_inventory'] = self._reader.set_cb_inventory(
            self._new_inventory_ignore)
        self._update_status(self.RUNNING, 'running')

    def _reader_status_changed(self, status: Dict[str, Any]) -> None:
        self._update_status(status['status'], f"Reader - {status['message']}", status['timestamp'])

    async def stop(self) -> None:
        """Stop the tunnel functionality"""
        if not self._is_started:
            return
        self._is_started = False
        # reset the reader callbacks
        self._reader.set_cb_input_changed(self._reader_org_values['cb_input_changed'])
        self._reader.set_cb_status(self._reader_org_values['cb_status'])
        self._reader.set_cb_inventory(self._reader_org_values['cb_inventory'])

        self._update_status(self.ERROR, 'stopped')

        if not self._reader_org_values['connected'] and self._reader.is_connected():
            # reader was not connected...so disconnect reader again
            await self._reader.disconnect()

    def set_tunnel_config(self, config: Optional[dict] = None) -> None:
        """Sets the tunnel config.

        Args:
            config (dict): configuration dictionary

        """
        if not config:
            return
        if 'input_start' in config:
            try:
                self._start_input = int(config['input_start'])
            except (TypeError, ValueError):
                self.get_logger().warning("The parameter 'input_start' is None or is not a int value.")

        if 'input_stop' in config:
            try:
                self._stop_input = int(config['input_stop'])
            except (TypeError, ValueError):
                self.get_logger().warning("The parameter 'input_stop' is None or is not a int value.")

    async def get_tunnel_config(self) -> dict:
        """Returns the tunnel configuration

        Returns:
            Dict[str, Any]: the tunnel configuration

        """
        config: Dict[str, Any] = {}
        config['input_start'] = self._start_input
        config['input_stop'] = self._stop_input
        return config

    def _new_inventory(self, inventory: List[Tag]) -> None:
        for tag in inventory:
            stored_tag: Optional[Tag] = self._current_scan['tags'].get(tag.get_id())
            if stored_tag:
                stored_tag.set_last_seen(tag.get_timestamp())
                stored_tag.set_seen_count(stored_tag.get_seen_count() + tag.get_seen_count())
            else:
                tag.set_first_seen(tag.get_timestamp())
                self._current_scan['tags'][tag.get_id()] = tag

    def _new_inventory_ignore(self, inventory: List[Tag]) -> None:
        self.get_logger().debug("Inventory report received, but reader stopped - %s", inventory)

    def _input_changed(self, pin: int, new_value: bool) -> None:
        self.get_logger().debug("Input %s changed to %s", pin, new_value)
        if pin == self._start_input:
            if new_value == self._start_trigger_on_high:
                # start the scan
                asyncio.create_task(self._start_scan(self._last_scan['id'] + 1))
        elif pin == self._stop_input:
            if new_value == self._stop_trigger_on_high:
                # stop scan
                try:
                    asyncio.create_task(self._stop_scan(self._current_scan['id']))
                except KeyError:
                    self.get_logger().debug("Stop scan triggered, but no scan was started")

    async def _start_scan(self, scan_id: int) -> None:
        self.get_logger().debug("Start scan %s triggered", scan_id)
        if self._start_delay > 0:
            await asyncio.sleep(self._start_delay)
        if self._current_scan:
            if scan_id == self._current_scan.get('id'):
                # this can happen if a delay is used and the input is triggered multiple times
                self.get_logger().warning("The start of scan %s was triggered again!")
            else:
                self.get_logger().warning("Start triggered, but last scan not yet finished - start ignored")
            return
        self.get_logger().debug("Start scan %s", scan_id)
        try:
            await self._reader.start_inventory()
            self._current_scan = {'type': "scan", 'id': scan_id, 'start_time': time(), 'tags': {}}
            self._reader.set_cb_inventory(self._new_inventory)
        except RfidReaderException as err:
            self.get_logger().info("Error starting the scanning - %s", err)
            if self._reader.is_connected():
                self.get_logger().info("Retry to start the scanning - %s", err)
                asyncio.create_task(self._start_scan(self._current_scan['id']))

    async def _stop_scan(self, scan_id: int) -> None:
        self.get_logger().debug("Stop scan %s triggered", scan_id)
        if self._stop_delay > 0:
            await asyncio.sleep(self._stop_delay)
        self.get_logger().debug("Stop scan %s", scan_id)
        try:
            await self._reader.stop_inventory()
            self._current_scan['stop_time'] = time()
            # call new inventory event
            event: Dict[str, Any] = self._current_scan.copy()
            event['inventory'] = list(event['tags'].values())
            del event['tags']
            if self._cb_scan_finished:
                self._cb_scan_finished(event)
            self._reader.set_cb_inventory(self._new_inventory_ignore)
            self._last_scan = self._current_scan
            self._current_scan = {}
        except RfidReaderException as err:
            self.get_logger().info("Error stopping the scanning - %s", err)
            if self._reader.is_connected():
                self.get_logger().info("Retry to stop the scanning - %s", err)
                asyncio.create_task(self._stop_scan(scan_id))
