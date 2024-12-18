"""Uhf Tag tests
"""
from time import time
import unittest
from metratec_rfid.uhf_tag import UhfTag


class UhfTagTestCase(unittest.TestCase):
    """Uhf Tag test case
    """

    def setUp(self) -> None:
        # disable 'Useless super delegation' warning - pylint: disable=W0235
        return super().setUp()

    def test_zero(self) -> None:
        """Tests the default constructor
        """
        tag = UhfTag("")
        self.assertIsNotNone(tag.get_epc())
        self.assertEqual(0, tag.get_timestamp())
        self.assertEqual("", tag.get_tid())
        self.assertEqual(-1, tag.get_antenna())
        self.assertEqual(1, tag.get_seen_count())
        self.assertEqual(0, tag.get_rssi())

    def test_init(self) -> None:
        """Tests the constructor
        """
        timestamp = time()
        tag = UhfTag("EPC", timestamp, "TID", 1, 2, 12)
        self.assertEqual(tag.get_epc(), "EPC")
        self.assertEqual(tag.get("epc"), "EPC")
        self.assertEqual(tag.get_timestamp(), timestamp)
        self.assertEqual(tag.get("timestamp"), timestamp)
        self.assertEqual(tag.get_tid(), "TID")
        self.assertEqual(tag.get("tid"), "TID")
        self.assertEqual(tag.get_antenna(), 1)
        self.assertEqual(tag.get("antenna"), 1)
        self.assertEqual(tag.get_seen_count(), 2)
        self.assertEqual(tag.get("seen_count"), 2)
        self.assertEqual(tag.get_rssi(), 12)
        self.assertEqual(tag.get("rssi"), 12)

    def test_other_attributes(self) -> None:
        """Tests the not default initialised attributes
        """
        timestamp = time()
        tag = UhfTag("")

        tag.set_first_seen(timestamp)
        self.assertEqual(tag.get_first_seen(), timestamp)
        self.assertEqual(tag.get("first_seen"), timestamp)

        tag.set_last_seen(timestamp)
        self.assertEqual(tag.get_last_seen(), timestamp)
        self.assertEqual(tag.get("last_seen"), timestamp)

        tag.set_error_message("Warning")
        self.assertTrue(tag.has_error())
        self.assertEqual(tag.get_error_message(), "Warning")
        self.assertEqual(tag.get('error_message'), "Warning")

        tag.set_data("data")
        self.assertEqual(tag.get_data(), "data")
        self.assertEqual(tag.get('data'), "data")


if __name__ == '__main__':
    unittest.main()
