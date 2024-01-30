import unittest
from unittest.mock import patch
from scorepmetadata2json.__main__ import parse_args


class TestScorepmetadata2json(unittest.TestCase):
    @patch("argparse._sys.argv", ["scorepmetadata2json", "file.txt"])
    def test_parse_args_file(self):
        args = parse_args()
        self.assertEqual(args.file, "file.txt")
        self.assertFalse(args.schema)
        self.assertFalse(args.debug)

    @patch("argparse._sys.argv", ["scorepmetadata2json", "--schema"])
    def test_parse_args_schema(self):
        args = parse_args()
        self.assertTrue(args.schema)
        self.assertIsNone(args.file)
        self.assertFalse(args.debug)


if __name__ == "__main__":
    unittest.main()
