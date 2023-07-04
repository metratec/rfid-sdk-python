"""
socket connection
"""

import asyncio
import logging
import ssl
from typing import Optional, List
from os import path
from .connection import Connection


class SocketConnection(Connection, asyncio.Protocol):
    """
    Tcp input connection - establishes a connection to a tcp server.

    """
    # disable too many instance attributes warning - pylint: disable=R0902

    def __init__(self, address: str, port: int) -> None:
        """Create a new socket connection

        Args:
            address (str): The ip address

            port (int): the port to use.
        """
        super().__init__()
        self._log: logging.Logger = logging.getLogger("Input-"+address)
        self._address: str = address
        self._connection_type: str = "tcp"
        self._port: int = port
        self._ssl_cert_file: Optional[str] = None
        self._transport: Optional[asyncio.BaseTransport] = None
        # is true if the connection is established
        self._is_connected: bool = False
        self._reconnect_count: int = 0
        self._is_started: bool = False
        self._connect_task: Optional[asyncio.Task] = None
        self._last_message: bytes = b""
        self._separator_encoded: bytes = "\n".encode()

    def get_info(self) -> str:
        return f"{self._address}:{self._port}"

    def set_separator(self, separator: str) -> None:
        self._separator_encoded = separator.encode()

    def connect(self) -> None:
        """
        Connects the socket
        """
        if self._is_started:
            return
        self._is_started = True
        self._connect_task = asyncio.ensure_future(self._connect_to_server())

    async def _connect_to_server(self, delay=0) -> None:
        # disable catching general exception warning - pylint: disable=W0703
        # loop = asyncio.get_running_loop()  # python >= 3.7
        if delay > 0:
            await asyncio.sleep(delay)
        self._log.debug("connect to %s", self.get_info())
        # loop = asyncio.get_event_loop_policy().get_event_loop()  # python < 3.7
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        try:
            if self._connection_type == "tcp":
                ssl_cntx: Optional[ssl.SSLContext] = None
                if self._ssl_cert_file:
                    if path.exists(self._ssl_cert_file):
                        ssl_cntx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self._ssl_cert_file)
                        self._log.debug("use %s for ssl", self._ssl_cert_file)
                    else:
                        self._log.debug("cert file %s does not exist", self._ssl_cert_file)
                await loop.create_connection(lambda: self, self._address, self._port, ssl=ssl_cntx)
            elif self._connection_type == "udp":
                # TODO SSL for UDP
                await loop.create_datagram_endpoint(lambda: self, remote_addr=(self._address, self._port))
        except Exception as err:
            self._reconnect_count += 1
            if self._reconnect_count <= 10:
                wait_time: int = self._reconnect_count * 2
            else:
                wait_time = self._reconnect_count ** 3
            wait_time = min(wait_time, 600)
            await asyncio.sleep(wait_time)
            self.connection_lost(err)
            self._connect_task = asyncio.ensure_future(self._connect_to_server())

    def disconnect(self) -> None:
        """
        Disconnect the socket
        """
        if not self._is_started:
            return
        self._is_started = False
        if self._connect_task and not self._connect_task.done():
            self._connect_task.cancel()
        if self._is_connected:
            self._is_connected = False
            if self._transport:
                self._transport.close()
            self._transport = None

    def send(self, data) -> None:
        """
        Sends the data to the connected socket
        """
        if self._transport:
            self._transport.write(data)  # type: ignore

    def is_connected(self) -> bool:
        """ return True if the connection is established """
        return self._is_connected

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._is_connected = True
        self._reconnect_count = 0
        self._transport = transport
        if self._cb_connection_made:
            self._cb_connection_made()

    def data_received(self, data) -> None:
        messages: List[bytes] = self._parse_input_data(data)
        if self._cb_data_received:
            for message in messages:
                self._cb_data_received(message[:-1])

    def datagram_received(self, data: bytes, addr) -> None:
        """
        Called from the datagram endpoint when some data is received.

        The argument is a bytes object.
        """
        # disable unused argument warning - pylint: disable=W0613
        messages: List[bytes] = self._parse_input_data(data)
        if self._cb_data_received:
            for message in messages:
                self._cb_data_received(message[:-1])

    def _parse_input_data(self, recv_data: bytes) -> List[bytes]:
        """
        Adds the new data to the message buffer and checking for separators.

        Return a list with separated messages
        """
        self._last_message += recv_data
        responses: List[bytes] = []
        index: int = self._last_message.find(self._separator_encoded)
        while index > -1:
            responses.append(self._last_message[:index+1])
            self._last_message = self._last_message[index+1:]
            index = self._last_message.find(self._separator_encoded)
        return responses

    def error_received(self, exc) -> None:
        """
        Called from the datagram endpoint when a error occurs

        The argument is a error object.
        """
        self.connection_lost(exc)

    def connection_lost(self, exc) -> None:
        if exc is None:
            message: str = "connection lost" if self._is_connected else "disconnected"
        else:
            message = str(exc)
        self._log.debug("connection to %s - %s", self._address, message)
        if self._cb_connection_lost:
            self._cb_connection_lost(message)
        if self._is_connected:
            # reconnect
            self._is_connected = False
            self._connect_task = asyncio.ensure_future(self._connect_to_server(1))
