"""Uhf Tag tests
"""
from time import time
import random
from typing import List
import unittest
from metratec_rfid.uhf_tag import UhfTag
from metratec_rfid.pulsar_lr import PulsarLR


class UhfTagTestCase(unittest.TestCase):
    """Uhf Tag test case
    """

    def setUp(self) -> None:
        # disable 'Useless super delegation' warning - pylint: disable=W0235
        return super().setUp()

    def test_inventory_parsing(self) -> None:
        """Tests tag parsing
        """
        # disable 'protected-access' warning - pylint: disable=W0212
        reader = PulsarLR("", "192.168.2.203")  # any IP - is not needed
        # prepare reader
        reader._config['inventory'] = {}
        reader._config['inventory']['with_tid'] = True
        reader._config['inventory']['with_rssi'] = True

        tags = self._generate_uhf_tags()
        # prepare reader response
        response = []
        for tag in tags:
            response.append(f"+INV: {tag.get_epc()},{tag.get_tid()},{tag.get_rssi()}")
        # call reader response parser
        inv = reader._parse_inventory(response, time())
        # check parsed response
        self.assertEqual(len(tags), len(inv))
        self.assertTrue(any(item.get_epc() == tags[0].get_epc() for item in inv if isinstance(item, UhfTag)))
        for item in inv:
            self.assertIsInstance(item, UhfTag)
            for tag in tags:
                if item.get_id() == tag.get_id():
                    self.assertIsNotNone(item.get_tid())
                    self.assertEqual(item.get_tid(), tag.get_tid())
                    self.assertIsNotNone(item.get("rssi"))
                    self.assertEqual(item.get("rssi"), tag.get("rssi"))
                    break
            else:
                self.fail(f"Unexpected tag {item.get_id()} - not in original list")

    # def test_inventory_report_parsing(self) -> None:
    #     """Tests tag parsing
    #     """
    #     # disable 'protected-access' warning - pylint: disable=W0212
    #     reader = PulsarLR("", "192.168.2.203")  # any IP - is not needed
    #     # prepare reader
    #     reader._config['inventory_report'] = {}
    #     reader._config['inventory_report']['id'] = 'EPC'

    #     tags = self._generate_uhf_tags()
    #     # prepare reader response
    #     response = []
    #     for tag in tags:
    #         response.append(f"+INVR: {tag.get_epc()},{tag.get_seen_count()}")
    #     # call reader response parser
    #     inv = reader._parse_inventory_report(response, time())
    #     # check parsed response
    #     self.assertEqual(len(tags), len(inv))
    #     for item in inv:
    #         self.assertIsInstance(item, UhfTag)
    #         for tag in tags:
    #             if item.get_id() == tag.get_id():
    #                 self.assertIsNotNone(item.get_seen_count())
    #                 self.assertEqual(item.get_seen_count(), tag.get_seen_count())
    #                 break
    #         else:
    #             self.fail(f"Unexpected tag {item.get_id()} - not in original list")

    def _generate_uhf_tags(self, count: int = 10) -> List[UhfTag]:
        """Generate a tag list"""
        letters = "0123456789ABCDEF"
        tags = []
        for _ in range(0, count):
            epc = "".join(random.choice(letters) for _ in range(8))
            tid = "".join(random.choice(letters) for _ in range(16))
            rssi = random.randint(-128, -40)
            seen_count = random.randint(1, 10)
            tags.append(UhfTag(epc, tid=tid, rssi=rssi, seen_count=seen_count))
        return tags

    def test_tag_list(self) -> None:
        """ Test Tag lists """
        tags = self._generate_uhf_tags(2)
        self.assertEqual(2, len(tags))
        for tag in tags:
            self.assertIsNotNone(tag.get_epc())
            self.assertEqual(8, len(tag.get_epc()))  # type: ignore
            self.assertIsNotNone(tag.get_tid())
            self.assertEqual(16, len(tag.get_tid()))  # type: ignore


if __name__ == '__main__':
    unittest.main()
