# disable 'docstring' warning - pylint: disable=C0114,C0115,C0116
# disable 'wrong-import-position' warning - pylint: disable=C0413
import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import sys
import time
import datetime


sys.path.append(os.getcwd())
# print(sys.path)
from metratec_rfid.connection.serial_connection import SerialConnection  # noqa -- flake ignore
from metratec_rfid import RfidReaderException  # noqa -- flake ignore
from metratec_rfid import UhfReaderGen2  # noqa -- flake ignore

READER_PORT = "/dev/ttyACM0"
EXPECTED_TAG = "E2806894000040195933A511"
REPORT_INTERVAL = 60


class TestReader:
    """ Test Reader class """
    # disable 'Too few public methods' warning - pylint: disable=R0903

    def __init__(self, port: str = READER_PORT) -> None:
        self._logger = logging.getLogger("TestReader")
        self._reader = UhfReaderGen2("Reader", SerialConnection(port))
        # self._reader.set_cb_inventory(self._cb_inventory)
        # self._reader.set_cb_inventory_report(self._cb_inventory)
        # self._reader.set_cb_status(self._cb_status)

    async def run(self):
        # Disable 'Catching too general exception' warning: pylint: disable=W0703
        count = 0
        no_tag_found = 0
        wrong_epc = 0
        report_time = time.time() + REPORT_INTERVAL
        while True:
            with open("output.txt", "a", encoding='ascii') as file:
                try:
                    self._logger.info("Connect reader")
                    await self._reader.connect(30.0)
                    self._logger.info("Reader connected")
                    await self._reader.set_inventory_settings(False, False, True)
                    while self._reader.is_connected():
                        tags = await self._reader.get_inventory()
                        count += 1
                        if len(tags) == 0:
                            no_tag_found += 1
                            continue
                        if EXPECTED_TAG != tags[0].get_id():
                            wrong_epc += 1
                            print(f"Wrong epc: {tags[0].get_id()}")
                        if report_time <= time.time():
                            msg = (
                                f"{datetime.datetime.now()} Count: {count} - Wrong epc: {wrong_epc}"
                                f" - no tags: {no_tag_found}"
                            )
                            print(msg)
                            file.write(f"{msg}\n")
                            file.flush()
                            report_time += REPORT_INTERVAL

                except Exception as err:
                    self._logger.error("Exception: %s", str(err))
                finally:
                    try:
                        await self._reader.disconnect()
                    except RfidReaderException as err:
                        self._logger.error("Error disconnect - %s", err)


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
    ch.setLevel(logging.INFO)
    ch.setFormatter(stdout_formatter)
    logger.addHandler(ch)
    logging.getLogger().info("Program started")
    asyncio.get_event_loop().run_until_complete(TestReader().run())
    logging.getLogger().info("Program finished")
