# disable 'docstring' warning - pylint: disable=C0114,C0115,C0116
# disable 'wrong-import-position' warning - pylint: disable=C0413
import asyncio
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import random
import sys
sys.path.append(os.getcwd())
# print(sys.path)
from metratec_rfid import RfidReaderException  # noqa -- flake ignore
from metratec_rfid import PulsarLR  # noqa -- flake ignore

# READER_IP = '192.168.2.152'
READER_IP = '127.0.0.1'


class TestReader:
    """ Test Reader class """

    def __init__(self, ip_address: str) -> None:
        self._logger = logging.getLogger("TestReader")
        self._reader = PulsarLR("Pulsar", ip_address)
        self._reader.set_cb_inventory(self._cb_inventory)
        self._reader.set_cb_inventory_report(self._cb_inventory)
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
        # self._logger.info("Test Info")
        # info = await self._reader.get_reader_info()
        # if "PULSAR_LR" not in info['firmware']:
        #     raise RfidReaderException(f"firmware error {info['firmware']}")
        # if "01" not in info['firmware_version']:
        #     raise RfidReaderException(f"firmware version error {info['firmware_version']}")
        # # if info['hardware'] != "PulsarLR":
        # #     raise Exception("hardware error")
        # if "01" not in info['hardware_version']:
        #     raise RfidReaderException("hardware version error")
        # if not info['serial_number']:
        #     raise RfidReaderException("serial number error")
        self._logger.info("Test Output")
        outputs = await self._reader.get_outputs()
        for pin, value in outputs.items():
            await self._reader.set_output(pin, not value)
            if value == await self._reader.get_output(pin):
                raise RfidReaderException("Set output error")
            await self._reader.set_output(pin, value)

        self._logger.info("Test REG")
        region_org = await self._reader.get_region()
        await self._reader.set_region("ETSI")
        if "ETSI" != await self._reader.get_region():
            raise RfidReaderException("ETSI error")
        await self._reader.set_region("ETSI_HIGH")
        if "ETSI_HIGH" != await self._reader.get_region():
            raise RfidReaderException("ETSI_HIGH error")
        await self._reader.set_region(region_org)

        self._logger.info("Test Power")
        power_org = await self._reader.get_antenna_power(1)
        for power in range(0, 31):
            await self._reader.set_antenna_power(1, power)
            if power != await self._reader.get_antenna_power(1):
                raise RfidReaderException("POWER error")
        await self._reader.set_antenna_power(1, power_org)

        tag_size = await self._reader.get_tag_size()
        await self._reader.set_tag_size(tag_size)
        tag_size2 = await self._reader.get_tag_size()
        if tag_size != tag_size2:
            raise RfidReaderException("Tag Size error")

    async def test_inventory(self):
        """ test inventory
        """
        await self._reader.set_antenna(2)
        settings = await self._reader.get_inventory_settings()
        await self._reader.set_inventory_settings(True, True, True)
        inventory = await self._reader.get_inventory()
        for tag in inventory:
            print(json.dumps(tag))
        inventory = await self._reader.get_inventory()
        for tag in inventory:
            print(json.dumps(tag))
        await self._reader.set_inventory_settings(settings.get('only_new_tag', False),
                                                  settings.get('with_rssi', False),
                                                  settings.get('with_tid', False))
        inventory = await self._reader.get_inventory()
        for tag in inventory:
            print(json.dumps(tag))

    async def test_inventory_multi(self):
        """ test inventory
        """
        await self._reader.set_antenna_multiplex(4)
        settings = await self._reader.get_inventory_settings()
        await self._reader.set_inventory_settings(False, True, True)
        inventory = await self._reader.get_inventory_multi(ignore_error=True)
        for tag in inventory:
            print(json.dumps(tag))
        await self._reader.set_inventory_settings(settings.get('only_new_tag', False),
                                                  settings.get('with_rssi', False),
                                                  settings.get('with_tid', False))
        inventory = await self._reader.get_inventory_multi(ignore_error=True)
        for tag in inventory:
            print(json.dumps(tag))

    async def test_inventory_report(self):
        """ test inventory
        """
        await self._reader.set_antenna(2)
        settings = await self._reader.get_inventory_settings()
        await self._reader.set_inventory_settings(True, True, True)
        inventory = await self._reader.get_inventory_report()
        for tag in inventory:
            print(json.dumps(tag))
        await self._reader.set_inventory_settings(settings.get('only_new_tag', False),
                                                  settings.get('with_rssi', False),
                                                  settings.get('with_tid', False))

    async def test_continuous_inventory(self, duration: float = 10.0):
        """ test continuous inventory
        """
        # await self._reader.set_antenna(2)
        await self._reader.set_antenna_multiplex(4)
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
        await self._reader.set_antenna(antenna)
        inventory = await self._reader.read_tag_data()
        for tag in inventory:
            print(json.dumps(tag))

        inventory = await self._reader.read_tag_data(epc_mask='E200', length=8)
        for tag in inventory:
            print(json.dumps(tag))

        inventory = await self._reader.read_tag_tid()
        for tag in inventory:
            print(json.dumps(tag))

        # self._logger.info("read data: %s", inventory)

    async def test_write_data(self, data: str, epc_mask: str, antenna: int = 1):
        """ test write data
        """
        await self._reader.set_antenna(antenna)
        await self._reader.set_mask(epc_mask)
        inventory = await self._reader.read_tag_data()
        for tag in inventory:
            print(json.dumps(tag))
        inventory = await self._reader.write_tag_data(data, 0)
        for tag in inventory:
            print(json.dumps(tag))
        await self._reader.reset_mask()

    async def test_write_epc(self, tid: str, new_epc: str, antenna: int = 1):
        """ test write epc
        """
        await self._reader.set_antenna(antenna)
        inventory = await self._reader.read_tag_tid()
        for tag in inventory:
            print(json.dumps(tag))
        inventory = await self._reader.write_tag_epc(tid, new_epc)
        for tag in inventory:
            print(json.dumps(tag))
        inventory = await self._reader.read_tag_tid()
        for tag in inventory:
            print(json.dumps(tag))

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
        print(await self._reader.send_custom_command("AT+PWR=12"))

    async def test_antenna_multiplex(self):
        mux = await self._reader.get_antenna_multiplex()
        await self._reader.set_antenna_multiplex(4)
        await self._reader.set_antenna_multiplex([1, 2, 3, 4])
        await self._reader.set_antenna_multiplex(mux)

    async def test_new_commands(self):
        # High on Tag
        data_org = await self._reader.get_high_on_tag_output()
        for value in range(1, 5):
            duration_tmp = random.randint(10, 1000)
            await self._reader.set_high_on_tag_output(value, duration_tmp)
            data = await self._reader.get_high_on_tag_output()
            if value != data['pin']:
                raise RfidReaderException("Set high on tag error")
            if duration_tmp != data['duration']:
                raise RfidReaderException("Set high on tag duration error")
            if not data['enable']:
                raise RfidReaderException("Is high on tag error")
        await self._reader.disable_high_on_tag()
        data = await self._reader.get_high_on_tag_output()
        if data['enable']:
            raise RfidReaderException("high on tag not deactivated")
        if data_org['enable']:
            await self._reader.set_high_on_tag_output(data_org['pin'], data_org['duration'])

        # Authenthicate Server
        data = await self._reader.call_impinj_authentication_service()
        print(data)

        # Inventory settings
        settings_org = await self._reader.get_inventory_settings()
        await self._reader.set_inventory_settings(True, True, True, True)
        settings = await self._reader.get_inventory_settings()
        if not settings['only_new_tag']:
            raise RfidReaderException("Setting error")
        if not settings['with_rssi']:
            raise RfidReaderException("Setting error")
        if not settings['with_tid']:
            raise RfidReaderException("Setting error")
        if not settings['fast_start']:
            raise RfidReaderException("Setting error")
        await self._reader.set_inventory_settings(settings_org['only_new_tag'],
                                                  settings_org['with_rssi'],
                                                  settings_org['with_tid'],
                                                  settings_org['fast_start'])
        settings = await self._reader.get_inventory_settings()
        if settings_org['only_new_tag'] != settings['only_new_tag']:
            raise RfidReaderException("Setting error")
        if settings_org['with_rssi'] != settings['with_rssi']:
            raise RfidReaderException("Setting error")
        if settings_org['with_tid'] != settings['with_tid']:
            raise RfidReaderException("Setting error")
        if settings_org['fast_start'] != settings['fast_start']:
            raise RfidReaderException("Setting error")

        # Test session
        session_org = await self._reader.get_selected_session()
        for session in ['0', '1', '2', '3', 'AUTO']:
            await self._reader.set_selected_session(session)
            tmp = await self._reader.get_selected_session()
            if tmp != session:
                raise RfidReaderException("Session error")
        await self._reader.set_selected_session(session_org)


async def main():
    """ main
    """
    # Disable 'Catching too general exception' warning: pylint: disable=W0703
    test = TestReader(READER_IP)
    all_ok = True
    try:
        await test.connect()
        await test.test_antenna_multiplex()
        # await test.test_new_commands()
        # await asyncio.sleep(2.0)
        # await test.connect()

        await test.test_simple()

        await test.test_settings()
        await test.test_inventory()
        # await test.test_continuous_inventory(2)
        await test.test_inventory_multi()
        # await test.test_continuous_inventory_multi()
        await test.check_antenna()
        # await test.test_inventory_report()
        # await test.test_read_data(2)
        # await test.test_write_data("3034", "3034", 4)
        # await test.test_write_epc("E280689420004019", "ABCD1234", 4)
        await test.test_io()
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
