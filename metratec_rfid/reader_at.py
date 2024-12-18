""" metratec at reader
"""
from abc import abstractmethod
import asyncio
import logging
from time import time
from typing import Optional, Any,  Dict, List

from .reader_exception import RfidReaderException
from .reader import RfidReader
from .connection.connection import Connection


class ReaderAT(RfidReader):
    """The implementation of the AT reader protocol
    """
    # disable 'Too many public methods' warning - pylint: disable=R0904
    # disable 'Too many instance attributes' warning - pylint: disable=R0902

    def __init__(self, instance: str, connection: Connection) -> None:
        super().__init__(connection, instance)
        self._connection.set_separator("\n")
        self._communication_lock = asyncio.Lock()
        self._config: dict = {}
        self._ignore_errors = False
        self._echo_enabled = False

    # @override
    async def get_reader_info(self) -> Dict[str, str]:
        command: str = "ATI"
        response: List[str] = await self._send_command(command)
        # +SW: PULSAR_LR 0100
        # +HW: PULSAR_LR 0100
        # +SERIAL: 2020090817420000
        try:
            firmware: List[str] = response[0].split(" ")
            hardware: List[str] = response[1].split(" ")
            serial: List[str] = response[2].split(" ")
            info: Dict[str, str] = {
                'firmware': firmware[1],
                'firmware_version': firmware[-1],
                'hardware': hardware[1],
                'hardware_version': hardware[-1],
                'serial_number': serial[1]}
            return info
        except IndexError as exc:
            raise RfidReaderException(
                f"Wrong reader - Not expected info response - {response}") from exc

    # @override
    async def set_antenna(self, antenna: int) -> None:
        await self._send_command("AT+ANT", antenna)
        self._config['antenna'] = antenna

    # @override
    async def get_antenna(self) -> int:
        try:
            response: List[str] = await self._send_command("AT+ANT?")
        except RfidReaderException as error:
            if "ERROR" in str(error):
                raise RfidReaderException("Multiple antennas not supported") from error
            raise error
        # +ANT: 2
        try:
            return int(response[0][6:])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+ANT? - {response}") from exc

    # @override
    async def start_inventory(self) -> None:
        await self._send_command('AT+CINV')

    # @override
    async def stop_inventory(self) -> None:
        try:
            await self._send_command('AT+BINV')
        except RfidReaderException as err:
            if "is not running" in str(err):
                return
            raise err

    async def get_temperature(self) -> Dict[str, int]:
        """Get temperature readings from device sensors.

        Returns measurements in degrees celsius for CPU, RF and PA.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, int]: Temperature measurements with keys
            "CPU", "RF" and "PA".
        """
        responses: List[str] = await self._send_command("AT+TEMP")
        # AT+TEMP
        # +TEMP: 30,50,40
        data: List[str] = responses[0][7:].split(',')
        try:
            config: Dict[str, int] = {'CPU': int(data[0]),
                                      'RF': int(data[1]),
                                      'PA': int(data[2])
                                      }
            return config
        except IndexError as e:
            raise RfidReaderException(
                f"Not expected response for command AT+TEMP - {responses}") from e

    # @override
    # FIXME move to IO
    async def enable_input_events(self, enable: bool = True) -> None:
        try:
            await self._send_command("AT+IEV", 1 if enable else 0)
        except RfidReaderException as err:
            raise RfidReaderException("Inputs not available") from err

    async def set_heartbeat(self, interval: int) -> None:
        await self._send_command("AT+HBT", interval)
        await super().set_heartbeat(interval)

    async def send_custom_command(self, command: str, timeout: float = 2.0) -> List[str]:
        """Send an arbitrary AT command to the reader and return the response.

        Reference the Metratec UHF AT Protocol Guide for information
        about the underlying AT commands.

        Args:
            command (str): The AT command to send.

            timeout (float, optional): The response timeout. Defaults to 2.0 seconds.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            list[str]: Line-by-line list of the reader response. In case
            of a set-command (e.g. AT+PWR=5) the list will be empty.

        Example:
            >>> res = send_custom_command("AT+Q?")
            >>> print(res[0])
            +Q: 2,0,10
        """
        return await self._send_command(command=command, timeout=timeout)

    # TODO
    async def check_antennas(self) -> None:
        """Check the antennas
        """
        # disable callback
        current_callback = self.set_cb_inventory(None)
        current_antenna = await self.get_antenna()
        has_errors = False
        antennas: List[int] = []
        try:
            errors = self._config.get('error', {})
            for antenna in range(1, 5):
                await self.set_antenna(antenna)
                try:
                    await self.get_inventory()
                    if f"Antenna {antenna}" in errors:
                        del errors[f"Antenna {antenna}"]
                except RfidReaderException:
                    # antenna has error
                    has_errors = True
                    antennas.append(antenna)
            if not has_errors:
                if 'error' in self._config:
                    del self._config['error']
                if self._status['status'] == RfidReader.ERROR:
                    self._update_status(RfidReader.RUNNING, "running")
        except RfidReaderException as err:
            raise err
        finally:
            self.set_cb_inventory(current_callback)
            await self.set_antenna(current_antenna)
        if has_errors:
            raise RfidReaderException(f"Antenna error: {' '.join(str(x) for x in antennas)}")

    ###############################################################################################
    # Abstract internal methods
    ###############################################################################################

    @abstractmethod
    def _handle_inventory_events(self, msg: str, timestamp: float) -> None:
        """handle inventory event message

        Args:
            msg (str): message
            timestamp (float): timestamp
        """

    ###############################################################################################
    # Internal methods
    ###############################################################################################

    def _parse_error_response(self, response: str) -> RfidReaderException:
        """analyse the reader error and return the resulting exception

        Args:
            response (str): error response

        Returns:
            RfidReaderException: resulting exception
        """
        return RfidReaderException(response)

    # @override
    def _data_received_config(self, data: str, timestamp: float) -> None:
        msg: str = data[:-1]
        if self.get_logger().isEnabledFor(logging.DEBUG):
            self.get_logger().debug("recv %s", msg.replace('\r', ' '))
        if not msg:
            return
        if msg[0] == '+':
            # ignore events
            if msg[1] == 'C':  # +CINV +CINVR
                return
            if msg[1] == 'H' and len(msg) == 4:  # +HBT
                return
        self._add_data_to_receive_buffer(msg)

    # @override
    def _data_received(self, data: str, timestamp: float) -> None:
        # disable 'Too many return statements' warning - pylint: disable=R0911
        # disable 'Too many branches' warning - pylint: disable=R0912
        msg: str = data[:-1]
        if self.get_logger().isEnabledFor(logging.DEBUG):
            self.get_logger().debug("recv %s", msg.replace('\r', ' '))
        if not msg:
            return
        if msg[0] == '+':
            # check if it is an event
            if msg[1] == 'C':  # +CINV +CINVR
                # continuous inventory event
                if msg[2] == 'I':  # +CINV +CINVR
                    self._handle_inventory_events(msg, timestamp)
                    return
            if msg[1] == 'H' and len(msg) == 4:  # +HBT
                # Heartbeat - ignore
                return
            if msg[1] == 'I' and msg[2] == 'E':  # +IEV
                # +IEV: 1,HIGH
                # +IEV: 2,LOW
                self._fire_input_changed_event(int(msg[6]), "HIGH" in msg[8:])
                return
        self._add_data_to_receive_buffer(msg)

    async def _send_command(self, command: str, *parameters: Any, timeout: float = 2.0) -> List[str]:
        """Send a command to the reader and return the response

        Args:
            command (str): the command

            parameters (str, optional): the command parameters

            timeout (float, optional): The response timeout. Defaults to 2.0.

        Raises:
            RfidReaderException: The reader response with an error

        Returns:
            list[str]: The reader responses. In case of an set command the list is empty
        """
        # disable 'Too many branches' warning - pylint: disable=R0912
        # disable 'Too many nested blocks' warning - pylint: disable=R1702
        await self._communication_lock.acquire()
        try:
            self._clear_response_buffer()
            send_command = self._prepare_command(command, *parameters)
            self.get_logger().debug("send %s", send_command)
            self._send(send_command+"\r")
            if self._echo_enabled:
                try:
                    resp: str = await self._recv(timeout)
                except TimeoutError as err:
                    msg: str = "Reader not " + ("responding" if self.get_status()["status"] >= 1 else "connected")
                    raise RfidReaderException(msg) from err
                if send_command not in resp:
                    raise RfidReaderException(
                        f"Not expected response for {send_command} - {resp}")
            max_time: float = time() + timeout
            response: str = ""
            try:
                while True:
                    resp = await self._recv(timeout)
                    if resp is None:
                        break
                    if resp == 'OK':
                        return response.split("\r") if response else []
                    if resp == 'ERROR':
                        try:
                            msg = response[response.rindex(
                                "<")+1:response.rindex(">")]
                            raise self._parse_error_response(msg)
                        except ValueError:
                            msg = f"{command} ERROR"
                        raise RfidReaderException(str(msg))
                    response = resp
                    if max_time <= time():
                        break
            except TimeoutError:
                pass
            if not response:
                raise RfidReaderException(
                    f"No reader response for command {send_command}")
            raise RfidReaderException(
                f"Wrong response for command {send_command} - {str(response)}")
        except AttributeError as err:
            self.get_logger().debug("send command error - %s", err)
            raise RfidReaderException("Reader not connected") from err
        finally:
            self._communication_lock.release()

    def _prepare_command(self, command: str, *parameters: Any) -> str:
        # prepare the command with the AT protocol style
        if not parameters:
            return command
        return command + "=" + ",".join(str(x) for x in parameters if x is not None)

    async def _enable_command_echo(self):
        self._echo_enabled = False
        await self._send_command("ATE1")
        self._echo_enabled = True

    async def _prepare_reader_communication(self) -> None:
        """Override for prepare the reader for the communication"""
        await self._enable_command_echo()
        await self.stop_inventory()

    async def _config_reader(self) -> None:
        info = await self.get_reader_info()
        # only check reader if decorator is present
        expected = getattr(self, "_expected_reader", None)
        if expected:
            if expected.get('hardware_name', 'unknown').lower() not in info['hardware'].lower():
                raise RfidReaderException(
                    f"Wrong reader type! {expected.get('hardware_name','unknown')} expected, {info['hardware']} found")
            if expected.get('firmware_name', 'unknown').lower() not in info['firmware'].lower():
                raise RfidReaderException(f"Wrong reader firmware! {expected.get('firmware_name','unknown')} expected" +
                                          f", {info['firmware']} found")
            firmware_version = float(f"{info['firmware_version'][0:2]}.{info['firmware_version'][2:4]}")
            if firmware_version < expected.get('min_firmware', 1.0):
                raise RfidReaderException("Reader firmware version too low, please update! " +
                                          f"Minimum {expected.get('min_firmware')} expected, {firmware_version} found")
        self._config.update(info)
        try:
            self._config['antenna'] = await self.get_antenna()
        except RfidReaderException:
            self._config['antenna'] = 1
        # try:
        #     await self.check_antennas()
        # except RfidReaderException as err:
        #     self.get_logger().info("Antenna check: %s", err)


class ReaderATSound(ReaderAT):
    """Mixin for playing sounds.
    """
    # disable 'not overridden' warning - pylint: disable=W0223

    async def enable_start_up_sound(self):
        """Enable the start up sound.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+SUS", 1)

    async def disable_start_up_sound(self):
        """Disable the start up sound.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+SUS", 0)

    async def play_feedback(self, sequence_nr: int):
        """Play a preconfigured sequence.

        0: Startup jingle
        1: OK feedback
        2: ERROR feedback

        Args:
            sequence_nr (int): Sequence number to play.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+FDB", sequence_nr)

    async def play_notes(self, notes: str, repetitions: int, step_length: int):
        """Play a sequence of notes.

        The current maximum sequence length is 64.

        Args:
            notes (str): Encoded notes to be played. A note is always
                encoded by its name written as a capital letter and
                octave e.g. C4 or D5. Half-tone steps are encoded by
                adding a s or b to the note. For example Ds4 or Eb4.
                Note that Ds4 and Eb4 are basically the same note.
                A pause is denoted by a lowercase x.
            repetitions (int): Number of times the sequence should be repeated.
            step_length (int): Step length of a single step in the sequence

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+PLY", notes, repetitions, step_length)


class ReaderATIO(ReaderAT):
    """Mixin for Input/Output features
    """
    # disable 'not overridden' warning - pylint: disable=W0223

    async def get_inputs(self) -> Dict[int, bool]:
        """Return the current input pin states.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[int, bool]: Dictionary with input pin number and its
            state. True represents `HIGH`.
        """

        response: List[str] = await self._send_command("AT+IN?")
        # +IN: 1,LOW
        # +IN: 2,HIGH
        values: Dict[int, bool] = {}
        for msg in response:
            values[int(msg[5])] = "HIGH" in msg[7:]
        return values

    async def get_input(self, pin: int) -> bool:
        """Return the current state of a single input pin.

        Args:
            pin (int): Input pin number.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            bool: The input pin state where `True` means `HIGH`.
        """

        inputs: Dict[int, bool] = await self.get_inputs()
        value: Optional[bool] = inputs.get(pin)
        if value is None:
            raise RfidReaderException(f"Input pin {pin} not available")
        return value

    async def get_outputs(self) -> Dict[int, bool]:
        """Return the current output pin states.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[int, bool]: Dictionary with output pin number and its
            state. True represents `HIGH`.
        """

        response: List[str] = await self._send_command("AT+OUT?")
        # +OUT: 1,LOW
        # +OUT: 2,HIGH
        values: Dict[int, bool] = {}
        for msg in response:
            values[int(msg[6])] = "HIGH" in msg[8:]
        self._config['outputs'] = values
        return values

    async def get_output(self, pin: int) -> bool:
        """Return the current state of a single output pin.

        Args:
            pin (int): Output pin number.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            bool: The output pin state where `True` means `HIGH`.
        """

        outputs: Dict[int, bool] = await self.get_outputs()
        value: Optional[bool] = outputs.get(pin)
        if value is None:
            raise RfidReaderException(f"Output pin {pin} not available")
        return value

    async def set_outputs(self, outputs: Dict[int, bool]) -> None:
        """Set the defined output pin values.

        Args:
            outputs (dict): A dictionary where the keys specify the pin
                number and the corresponding value specifies the pin state.

        Raises:
            RfidReaderException: If a reader error occurs.
        """

        current = dict(self._config.get('outputs', await self.get_outputs()))
        for pin, value in outputs.items():
            current[pin] = value
        await self._send_command("AT+OUT",
                                 ",".join("" if x not in current else "HIGH" if current[x] else "LOW"
                                          for x in range(1, 5)))
        self._config['outputs'] = outputs

    async def set_output(self, pin: int, value: bool) -> None:
        """Set a single output pin value.

        Args:
            pin (int): Output pin number.

            value (bool): Output pin state to set.

        Raises:
            RfidReaderException: If a reader error occurs.
        """

        outputs = dict(self._config.get('outputs', await self.get_outputs()))
        outputs[pin] = value
        await self._send_command("AT+OUT",
                                 ",".join("" if x != pin else "HIGH" if value else "LOW" for x in range(1, 5)))
        self._config['outputs'] = outputs

    async def get_multiplexer(self, antenna_port: int) -> int:
        """Get the multiplexer size of an antenna port.

        Get the size of the multiplexer, i.e. the number antennas,
        connected to the specified physical antenna port of the device.

        Args:
            antenna_port (int): The antenna port to which the
                multiplexer is connected.

        Raises:
            RfidReaderException: If an error occurs.

        Returns:
            int: The multiplexer size.

        """
        connected_multiplexer = await self._get_connected_multiplexer()
        try:
            return connected_multiplexer[antenna_port - 1]
        except IndexError as e:
            max_port = len(connected_multiplexer)
            raise RfidReaderException(f"Wrong antenna port: {antenna_port} - [1,{max_port}] expected]") from e

    async def set_multiplexer(self, antenna_port: int, multiplexer_size: int):
        """Set the multiplexer size of an antenna port.

        Set the size of the multiplexer, i.e. the number of antennas,
        connected to the specified physical antenna port of the device.

        Args:
            antenna_port (int): The antenna port to which the
                multiplexer is connected
            multiplexer_size (int): The multiplexer size

        Raises:
            RfidReaderException: If an error occurs.

        """
        # get current setting from device
        connected_multiplexer = await self._get_connected_multiplexer()
        # change a single value
        try:
            connected_multiplexer[antenna_port - 1] = multiplexer_size
        except IndexError as e:
            max_port = len(connected_multiplexer)
            raise RfidReaderException(f"Wrong antenna port: {antenna_port} - [1,{max_port}] expected") from e
        # write new settings
        await self._set_connected_multiplexer(connected_multiplexer)

    async def get_high_on_tag_output(self) -> Dict[str, Any]:
        """Return the current settings of the "High On Tag" feature.

        Returns:
            Dict[str, Any]: Dictionary with 'enable', 'pin' and 'duration' entries.
        """
        responses = await self._send_command("AT+HOT?")
        # +HOT: 1
        # +HOT: OFF
        data: List[str] = responses[0][6:].split(',')
        if data[0] == 'OFF':
            return {'enable': False}
        # return int(data[0]), int(data[1])
        return {'enable': True, 'pin': int(data[0]), 'duration': int(data[1])}

    async def set_high_on_tag_output(self, output_pin: int, duration: int = 100):
        """Enable the "High On Tag" feature.

        This triggers the selected output to go to the `HIGH` state
        when a tag is inventoried. This allows triggering an external
        device whenever a tag is found.

        This corresponds to the blue LED on the device.

        Args:
            output_pin (int): Output pin index [1,4].
            duration (int, optional): `HIGH` duration in milliseconds
                [10, 10000]. Defaults to 100.

        """
        await self._send_command("AT+HOT", output_pin, duration)

    async def disable_high_on_tag(self):
        """Disable the "High On Tag" feature.

        """
        await self._send_command("AT+HOT", 0)

    ###############################################################################################
    # Internal methods
    ###############################################################################################

    async def _get_connected_multiplexer(self) -> List[int]:
        """the configured multiplexer size per antenna (index 0 == antenna 1)

        Returns:
            List[int]: with the configured multiplexer size
        """
        responses: List[str] = await self._send_command("AT+EMX?")
        # +EMX: 3,0,0,0
        data: List[str] = responses[0][6:].split(',')
        return [int(i) for i in data]

    async def _set_connected_multiplexer(self, connected_multiplexer: List[int]) -> None:
        """define the connected multiplexer

        Args:
            connected_multiplexer (List[int]): list with the multiplexer size for each antenna
        """
        await self._send_command("AT+EMX", *connected_multiplexer)
