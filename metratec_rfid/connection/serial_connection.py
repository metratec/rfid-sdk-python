""" serial connection """

import asyncio
import logging
from typing import Optional
from time import time
import serial
import serial_asyncio
from .connection import Connection


class SerialConnection(Connection):
    """Serial connection implementation
    """
    # disable 'too many instance attributes' warning - pylint: disable=R0902

    def __init__(
            self, port: str, baud_rate: int = 115200, parity=serial.PARITY_NONE,
            stop_bits: int = serial.STOPBITS_ONE, byte_size: int = serial.EIGHTBITS) -> None:
        """Create a new serial connection

        Args:
            port (str): The serial port.

            baud_rate (int, optional): The baudrate to use. Defaults to 115200.

            parity (_type_, optional): The parity to use. Defaults to serial.PARITY_NONE.

            stop_bits (int, optional): The stop bits to use. Defaults to serial.STOPBITS_ONE.

            byte_size (int, optional): The byte size to use. Defaults to serial.EIGHTBITS.
        """
        # disable 'Too many (positional) arguments' warning - pylint: disable=R0913,R0917
        super().__init__()
        self._logger: logging.Logger = logging.getLogger("Input-"+port)
        self._port: str = port
        self._baud_rate: int = baud_rate
        self._parity: str = parity
        self._stop_bits: int = stop_bits
        self._byte_size: int = byte_size
        self._min_reconnect_wait_time: float = 2.0
        self._max_reconnect_wait_time: float = 3600.0
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._separator_encoded: bytes = "\n".encode()
        self._is_started: bool = False
        self._internal_task: Optional[asyncio.Task] = None

    def get_port(self) -> str:
        """Return the port of the connection."""
        return self._port

    def set_port(self, port: str):
        """Set the port of the connection.

        New setting is only applied when not connected.
        """
        if not self.is_connected():
            self._port = port

    def get_info(self) -> str:
        return f"{self._port} ({self._baud_rate})"

    def set_separator(self, separator: str) -> None:
        if self._internal_task:
            self._internal_task.cancel()
            self._internal_task = asyncio.ensure_future(self._work())
        self._separator_encoded = separator.encode()

    def connection_made(self) -> None:
        """
        Called if the connection is established
        """
        if self._cb_connection_made:
            self._cb_connection_made()

    def connection_lost(self, err: Exception) -> None:
        """
        Called if the connection is lost
        """
        # print("connection lost " + str(err))
        if err is None:
            message: str = "connection lost" if self._writer else "disconnected"
        else:
            message = str(err)
        if self._cb_connection_lost:
            self._cb_connection_lost(message)
        self._logger.debug("connection to %s - %s", self._port, message)
        self._writer = None
        self._reader = None

    def data_received(self, data: bytes) -> None:
        """
        Called if data received

        Parameter:
        * data: received string
        """
        # self.log(logging.DEBUG, "data_received %s", data)
        # disable Catching too general exception Exception - pylint: disable=W0703
        if self._cb_data_received:
            try:
                self._cb_data_received(data)
            except Exception as err:
                self._logger.warning(
                    "Error in data received callback - %s", err, exc_info=True)

    def send(self, data) -> None:
        """
        Sends the data to the connected socket
        """
        if self._writer:
            self._writer.write(data)

    def is_connected(self) -> bool:
        """ return True if the connection is established """
        return self._writer is not None

    def connect(self) -> None:
        if self._is_started:
            return
        self._is_started = True
        self._internal_task = asyncio.ensure_future(self._work())

    def disconnect(self) -> None:
        if not self._is_started:
            return
        self._is_started = False
        if self._internal_task:
            self._internal_task.cancel()
        if self._writer:
            self._writer.close()
            self._writer = None
            self._reader = None

    async def _connect(self) -> None:
        retry_count = 0
        while self._is_started:
            try:
                self._reader, self._writer = await serial_asyncio.open_serial_connection(
                    url=self._port, baudrate=self._baud_rate, parity=self._parity,
                    stopbits=self._stop_bits, bytesize=self._byte_size)
                try:
                    self.connection_made()
                except (AttributeError, TypeError):
                    pass
                break
            except (FileNotFoundError, serial.SerialException) as err:
                # print(err)
                if self._cb_connection_lost:
                    self._cb_connection_lost(str(err))
                retry_count += 1
                if retry_count <= 10:
                    wait_until: float = self._min_reconnect_wait_time * retry_count
                else:
                    wait_until = self._min_reconnect_wait_time * \
                        retry_count ** 3
                    wait_until = min(wait_until, self._max_reconnect_wait_time)
                wait_until += time()
                while self._is_started and wait_until > time():
                    await asyncio.sleep(0.5)

    async def _work(self) -> None:
        while self._is_started:
            if not self._writer:
                await self._connect()
            while self._writer:
                # disable Catching too general exception Exception - pylint: disable=W0703
                try:
                    while self._reader:
                        msg: bytes = await self._reader.readuntil(self._separator_encoded)
                        # self._logger.debug("data received (config) %s",
                        #         msg.decode().replace("\r", "<CR>").replace("\n", "<LF>"))
                        self.data_received(msg[:-1])
                except serial.SerialException as err:
                    # print("exception consumed")
                    try:
                        self.connection_lost(err)
                    except (AttributeError, TypeError):
                        pass
                # except asyncio.exceptions.IncompleteReadError as err:  # not available in python 3.5
                #    self.debug("incomplete read error - %s", str(err))
                except Exception as err:
                    # self.warn("not extra caught exception: %s - %s", type(err), str(err), exc_info=1)
                    self._logger.info("Exception occurs - %s",
                                      str(err), exc_info=True)
                    try:
                        self.connection_lost(err)
                    except (AttributeError, TypeError):
                        pass
