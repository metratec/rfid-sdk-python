# disable 'docstring' warning - pylint: disable=C0114,C0115,C0116
# disable 'wrong-import-position' warning - pylint: disable=C0413
import asyncio
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import sys

sys.path.append(os.getcwd())
# print(sys.path)
from metratec_rfid.nfc_reader_at import Mode, NfcReaderAT  # noqa -- flake ignore
from metratec_rfid.connection.serial_connection import SerialConnection  # noqa -- flake ignore
from metratec_rfid import RfidReaderException  # noqa -- flake ignore

READER_PORT = "/dev/ttyACM0"


class TestReader:
    """ Test Reader class """

    def __init__(self, port: str) -> None:
        self._logger = logging.getLogger("TestReader")
        self._reader = NfcReaderAT("Reader", SerialConnection(port))
        self._reader._check_reader = False
        # expected = getattr(self._reader, "_expected_reader", {})
        # expected["hardware_name"] = "DESKID_NFC"
        # expected["firmware_name"] = "DESKID_NFC"

        self._reader.set_cb_inventory(self._cb_inventory)
        self._reader.set_cb_status(self._cb_status)
        # self._reader.set_cb_input_changed(self._cb_input_changed)
        self._reader.set_cb_input_changed(lambda pin, value: asyncio.ensure_future(self._cb_input_changed(pin, value)))

    def _cb_inventory(self, inventory):
        print(f"new inventory: {inventory}")

    def _cb_status(self, status):
        print(f"status changed: {status}")

    async def _cb_input_changed(self, pin, value):
        print(f"input changed: {pin} {value}")
        try:
            print(f"set output {pin} to {value}")
            await self._reader.set_output(pin, value)
            print(f"set output {pin+2} to {value}")
            await self._reader.set_output(pin+2, value)
        except RfidReaderException as err:
            print(f"Error set output {err}")

    async def connect(self):
        """ connect
        """
        self._logger.info("Connect reader")
        await self._reader.connect()
        self._logger.info("Reader connected")

    async def disconnect(self):
        """ disconnect
        """
        self._logger.info("Disconnect reader")
        await self._reader.disconnect()
        self._logger.info("Reader disconnected")

    async def test_settings(self) -> None:
        mode_org = await self._reader.get_mode()
        for mode in Mode:
            await self._reader.set_mode(mode)
            current = await self._reader.get_mode()
            if mode != current:
                raise RfidReaderException(f"Set Mode error - expected: {mode}, received:{current}")
        await self._reader.set_mode(mode_org)

    async def test_inventory(self):
        """ test inventory
        """
        # await self._reader.set_antenna(2)
        inventory = await self._reader.get_inventory()
        for tag in inventory:
            print(json.dumps(tag))
        inventory = await self._reader.get_inventory()
        for tag in inventory:
            print(json.dumps(tag))

    async def test_inventory_multi(self):
        """ test inventory
        """
        # await self._reader.set_antenna_multiplex(4)
        inventory = await self._reader.get_inventory_multi(ignore_error=True)
        for tag in inventory:
            print(json.dumps(tag))

    async def test_continuous_inventory(self, duration: float = 10.0):
        """ test continuous inventory
        """
        # await self._reader.set_antenna(2)
        # await self._reader.set_antenna_multiplex(4)
        await self._reader.start_inventory()
        await asyncio.sleep(duration)
        await self._reader.stop_inventory()

    async def test_continuous_inventory_multi(self, duration: float = 10.0):
        """ test continuous inventory
        """
        # await self._reader.set_antenna(2)
        await self._reader.set_antenna_multiplex(4)
        await self._reader.start_inventory_multi()
        await asyncio.sleep(duration)
        await self._reader.stop_inventory_multi()

    async def test_read_data(self, antenna: int = 1):
        """ test read data
        """

    async def test_write_data(self, data: str, epc_mask: str, antenna: int = 1):
        """ test write data
        """

    async def test_io(self):
        """ test io
        """
        outputs = await self._reader.get_outputs()
        print(f"Current: {outputs}")
        outputs[1] = False
        outputs[2] = False
        outputs[3] = False
        outputs[4] = False
        print(f"Set to: {outputs}")
        await self._reader.set_outputs(outputs)
        outputs = await self._reader.get_outputs()
        print(f"Current: {outputs}")

        for value in range(1, 5):
            await self._reader.set_output(value, True)
            print(f"Pin {value}: {await self._reader.get_output(value)}")

    async def check_antenna(self):
        await self._reader.check_antennas()

    async def test_simple(self) -> None:
        print(await self._reader.send_custom_command("ATI"))

    async def test_tag_detect(self) -> None:
        print(await self._reader.detect_tag_types())

    async def test_requests(self) -> None:
        try:
            print(await self._reader.send_read_request_iso15693("022B"))
        except RfidReaderException as err:
            print(f"Test request error: {err}")


async def main():
    """ main
    """
    # Disable 'Catching too general exception' warning: pylint: disable=W0703
    test = TestReader(READER_PORT)
    all_ok = True
    try:
        await test.connect()
        # await asyncio.sleep(2.0)
        # await test.connect()

        # await test.test_simple()

        # await test.test_settings()
        # await test.test_inventory()
        # await test.test_continuous_inventory(2)
        # await test.test_inventory_multi()

        # await test.test_tag_detect()
        await test.test_requests()
        # await test.test_continuous_inventory_multi()
        # await test.check_antenna()
        # await test.test_read_data(2)
        # await test.test_write_data("3034", "3034", 4)
        # await test.test_io()
    except Exception as err:
        all_ok = False
        logging.getLogger("Main").error("Exception: %s", str(err), exc_info=True)
        # logging.getLogger("Main").error(err, exc_info=True)
    finally:
        try:
            await test.disconnect()
        except RfidReaderException as err:
            logging.getLogger("Main").error("Error disconnect - %s", err)
    print(f'\n{"Done" if all_ok else "Done with errors!!!"}\n')


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(name)-21s %(levelname)-8s (%(module)s:%(lineno)d)  %(message)s')
    if not os.path.exists('logs'):
        os.makedirs('logs')
    fh = RotatingFileHandler('logs/logging.log', maxBytes=int(1e7), backupCount=10)
    fh.setFormatter(file_formatter)
    logger.addHandler(fh)

    stdout_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(name)-21s %(levelname)-8s (%(module)s:%(lineno)d)  %(message)s')
    ch = StreamHandler()
    ch.setFormatter(stdout_formatter)
    logger.addHandler(ch)
    logging.getLogger().info("Program started")
    asyncio.get_event_loop().run_until_complete(main())
    logging.getLogger().info("Program finished")
