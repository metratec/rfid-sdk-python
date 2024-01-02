""" metratec ascii reader
"""
from abc import abstractmethod
import asyncio
import time
from typing import Any, Dict, List

from .reader_exception import RfidReaderException
from .reader import RfidReader
from .reader import Connection


class ReaderGen1(RfidReader):
    """The implementation of the Ascii reader protocol
    """

    # disable 'Too many public methods' warning - pylint: disable=R0904
    # disable 'Too many instance attributes' warning - pylint: disable=R0902

    def __init__(self, instance: str, connection: Connection) -> None:
        super().__init__(connection, instance)
        self.get_connection().set_separator("\r")
        self._communication_lock = asyncio.Lock()
        self._config: dict = {}

    # @override
    def _data_received_config(self, data: str, timestamp: float) -> None:
        self.get_logger().debug("data received (config) %s",
                                data.replace("\r", "<CR>").replace("\n", "<LF>"))
        if not data:
            return
        if data[-1] == '\r':
            data = data[:-1]
        if data[0] == 'H' and data[2] == 'T':  # HBT
            return
        self._add_data_to_receive_buffer(data)

    async def send_custom_command(self, command: str) -> List[str]:
        """Send a command to the reader and return the response

        Args:
            command (str): the command

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[str]: The reader responses. In case of an set command the list is empty
        """
        response = await self._send_recv_command(command=command)
        return response.split('\r')

    async def _send_recv_command(self, command: str, *parameters) -> str:
        await self._communication_lock.acquire()
        try:
            self._send_command(command, *parameters)
            try:
                return await self._recv()
            except TimeoutError as err:
                raise TimeoutError("no reader response for command " + command + " " +
                                   " ".join(str(x) for x in parameters)) from err
        finally:
            self._communication_lock.release()

    async def _get_command(self, command: str, *parameters) -> str:
        return await self._send_recv_command(command, *parameters)

    async def _set_command(self, command: str, *parameters) -> None:
        await self._communication_lock.acquire()
        try:
            self._send_command(command, *parameters)
            try:
                response = await self._recv()
                if "OK" in response:
                    return
                raise RfidReaderException(f"{response} - ({command} {' '.join(str(x) for x in parameters if x)})")
            except TimeoutError as err:
                raise TimeoutError("no reader response for command " + command + " " +
                                   " ".join(str(x) for x in parameters)) from err
        finally:
            self._communication_lock.release()

    def _send_command(self, command: str, *parameters) -> None:
        data = self._prepare_command(command, *parameters)
        self.get_logger().debug("send data: %s", data.replace("\r", "<CR>"))
        self._send(self._prepare_command(command, *parameters))

    def _prepare_command(self, command: str, *parameters) -> str:
        if not parameters:
            payload = command+"\r"
        else:
            payload = command + " " + \
                " ".join(str(x) for x in parameters if x is not None) + "\r"
        return payload

    # @override
    async def connect(self, timeout: float = 5.0) -> None:
        self._connection.set_separator("\r")
        await super().connect(timeout)

    # @override
    async def _config_reader(self) -> None:
        # disable Too many branches warning - pylint: disable=R0912
        is_sleeping = False
        timeout: float = time.time() + 2.0
        self._send_command("BRK")
        while True:
            recv = await self._recv(0.5)
            if recv is None:
                is_sleeping = True
                self._send_command("WAK")
                timeout = time.time() + 2.0
            if "BRA" in recv:  # Continuous mode interrupted
                break
            if "NCM" in recv:  # Not in continuous mode
                break
            if "GMO" in recv:  # good morning
                is_sleeping = False
                break
            if "DNS" in recv:  # Did not sleep
                break
            if "CCE" in recv:
                if is_sleeping:
                    self._send_command("WAK 5E70")
                else:
                    self._send_command("COF 4F5E")
                timeout = time.time() + 2.0
                continue
            if "OK" in recv:  # "OK!" response to COF
                self._send_command("BRK")
                continue
            if "HBT" in recv:  # Heart beat
                continue
            if timeout < time.time():
                # Reader does not answer correctly
                self.get_logger().debug("wrong reader answer - %s", recv)
                raise RfidReaderException("Wrong metratec uhf device")

        # check reader
        # if not await self._is_supported():
        #     return

        await self._enable_end_of_frame()
        self._config.update(await self.get_reader_info())
        # prepare reader
        self._config['antenna_mode'] = "SINGLE"
        self._config['antenna'] = 0
        await self._prepare_reader()

    @abstractmethod
    async def _prepare_reader(self) -> None:
        """prepare the reader
        """

    async def _enable_end_of_frame(self):
        # enable end of frame:
        self.get_connection().set_separator("\n")
        self._send_command("EOF")  # end of frame
        while True:
            receive = await self._recv()
            if "OK" in receive:
                return

    # async def get_config(self) -> Dict[str, Any]:
    #     return self._config.copy()

    # async def set_config(self, config: Optional[Dict[str, Any]] = None) -> None:
    #     if config is not None:
    #         self._config = config

    async def set_heartbeat(self, interval: int) -> None:
        await self._set_command("HBT", interval)
        await super().set_heartbeat(interval)

    # @override
    async def get_inputs(self) -> Dict[int, bool]:
        values: Dict[int, bool] = {}
        for pin in range(0, 2):
            values[pin] = await self.get_input(pin)
        return values

    # @override
    async def get_input(self, pin: int) -> bool:
        response = await self._get_command("RIP", pin)
        if "HI" in response:
            return True
        if "LOW" in response:
            return False
        raise RfidReaderException(f"get input error - {response}")

    # @override
    async def get_outputs(self) -> Dict[int, bool]:
        raise RfidReaderException("not available")

    # @override
    async def set_outputs(self, outputs: Dict[int, bool]) -> None:
        for pin, value in outputs.items():
            await self.set_output(pin, value)

    # @override
    async def set_output(self, pin: int, value: bool) -> None:
        await self._set_command("WOP", pin, "HI" if value else "LOW")

    # @override
    async def get_output(self, pin: int) -> bool:
        raise RfidReaderException("not available")

    # @override
    async def enable_input_events(self, enable: bool = True) -> None:
        raise RfidReaderException(f"Input events not available for {self._config['firmware']}")

    # @override
    async def get_reader_info(self) -> Dict[str, Any]:
        info = {}
        response = await self._get_command("HWR")
        if "UCO" not in response:
            # DESKID_ISO      0200
            info['hardware'] = response[0:-5].strip()
            info['hardware_version'] = response[-5:-1]
            # DESKID_ISO      0312
            response = await self._get_command("RFW")
            info['firmware'] = response[0:-5].strip()
            info['firmware_version'] = response[-5:-1]
        else:
            response = await self._get_command("REV")
            # DESKID_ISO     01000218
            info['hardware'] = response[0:-8].strip()
            info['hardware_version'] = response[-8:-4]
            info['firmware'] = info['hardware']
            info['firmware_version'] = response[-4:]
        expected = getattr(self, "_expected_reader", {})
        if expected.get('hardware_name', 'unknown').lower() not in info['hardware'].lower():
            raise RfidReaderException(
                f"Wrong reader type! {expected.get('hardware_name','unknown')} expected, {info['hardware']} found")
        if expected.get('firmware_name', 'unknown').lower() not in info['firmware'].lower():
            raise RfidReaderException(f"Wrong reader firmware! {expected.get('firmware_name','unknown')} expected" +
                                      f", {info['firmware']} found")
        firmware_version = float(f"{info['firmware_version'][0:2]}.{info['firmware_version'][2:4]}")
        if firmware_version < expected.get('min_firmware', 1.0):
            raise RfidReaderException("Reader firmware too low, please update! " +
                                      f"Minimum {expected.get('min_firmware')} expected, {firmware_version} found")
        return info

    async def enable_antenna_report(self, enable: bool = True) -> None:
        """Enable the antenna report for inventory

        Args:
            enable (bool, optional): enable or disable. Defaults to True.
        """
        try:
            await self._set_command("SAP", "ARP", "ON" if enable else "OFF")
        except RfidReaderException as err:
            if "NOS" in str(err):
                raise RfidReaderException(f"Set antenna not supported by {self._config['firmware']}") from err
            raise err

    # @override
    async def set_antenna(self, antenna: int) -> None:
        try:
            await self._set_command("SAP", "MAN", antenna)
            self._config['antenna'] = antenna
            self._config['antenna_mode'] = "SINGLE"
        except RfidReaderException as err:
            if "NOS" in str(err):
                raise RfidReaderException(f"Set antenna not supported by {self._config['firmware']}") from err
            raise err

    async def set_antenna_outputs(self, pins: int) -> None:
        """Defines how many outputs are to be used for switching the antenna

        Args:
            pins (int): Number of outputs to be used
        """
        try:
            await self._set_command("SAP", "PIN", pins)
            self._config['antennas_pins'] = pins
        except RfidReaderException as err:
            if "NOS" in str(err):
                raise RfidReaderException(f"Set antenna not supported by {self._config['firmware']}") from err
            raise err

    # @override
    async def get_antenna(self) -> int:
        return self._config.get('antenna', -1)

    # @override
    async def set_antenna_multiplex(self, antennas: int, switch_delay: int = 0) -> None:
        await self._set_command("SAP", "AUT", antennas, switch_delay)
        self._config['multiplexing_antennas'] = antennas
        self._config['antenna_mode'] = "MULTIPLEX"

    # @override
    async def get_antenna_multiplex(self) -> int:
        return self._config.get('multiplexing_antennas', -1)

    @abstractmethod
    async def get_inventory(self, single_slot: bool = False, only_new_tags: bool = False):
        """get the current inventory from the current antenna (see set_antenna)

        Args:
            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[Tag]: An array with the founded transponder
        """

    # @override
    async def start_inventory(self, single_slot: bool = False, only_new_tags: bool = False) -> None:
        """Starts the continuos inventory. Multiple antennas are used (see set_antenna_multiplex)

        Args:
            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        if self._config['antenna_mode'][0] != "S":
            # Not in single antenna mode ... switch mode
            await self.set_antenna(await self.get_antenna())
        self._send_command("CNR INV", "SSL" if single_slot else None, "ONT" if only_new_tags else None)

    # @override
    async def stop_inventory(self) -> None:
        response = await self._get_command("BRK")
        if "BRA" in response or "NCM" in response:
            return
        raise RfidReaderException(f"Inventory not stopped - ({response})")

    @abstractmethod
    async def get_inventory_multi(self, ignore_error: bool = False, single_slot: bool = False,
                                  only_new_tags: bool = False):
        """get the current inventory. Multiple antennas are used (see set_antenna_multiplex)

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.

            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.
        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[Tag]: An array with the founded transponder
        """

    # @override
    async def start_inventory_multi(self, ignore_error: bool = False, single_slot: bool = False,
                                    only_new_tags: bool = False) -> None:
        """Starts the continuos inventory. Multiple antennas are used (see set_antenna_multiplex)

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.

            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        if self._config['antenna_mode'][0] != "M":
            # Not in multiplex antenna mode ... switch mode
            await self.set_antenna_multiplex(await self.get_antenna_multiplex())
        self._send_command("CNR INV", "SSL" if single_slot else None, "ONT" if only_new_tags else None)

    # @override
    async def stop_inventory_multi(self) -> None:
        await self.stop_inventory()

    @abstractmethod
    def _parse_inventory(self, data: str) -> None:
        """parse the inventory response

        Args:
            data (str): inventory response
        """

    async def reset(self):
        """Reset the reader
        """
        await self._set_command("RST")
        await asyncio.sleep(0.1)
        await self.connect()
