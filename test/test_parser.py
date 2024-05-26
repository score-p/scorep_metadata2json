import unittest
import os
from unittest.mock import patch
from io import StringIO
from scorepmetadata2json.__main__ import main


class TestScorepmetadata2json(unittest.TestCase):

    def setUp(self):
        """Setup test resources."""
        self.test_data_path = os.path.join(os.path.dirname(__file__), "test_data", "scorep.fair")
        self.reference_data_path = os.path.join(os.path.dirname(__file__), "test_data", "scorep.fair.json")
        self.mock_stdout = StringIO()

    def tearDown(self):
        """Cleanup test resources."""
        self.mock_stdout.close()

    def test_main(self):
        """Test main function output against known good data."""
        with patch("sys.argv", ["scorepmetadata2json", self.test_data_path]), \
             patch("sys.stdout", new=self.mock_stdout):
            main()
            self.assertFileContentEqual(self.mock_stdout.getvalue(), self.reference_data_path)

    def assertFileContentEqual(self, actual_content, expected_file_path):
        """Assert that the actual content is equal to the content of the expected file."""
        with open(expected_file_path, "r") as expected_file:
            expected_content = expected_file.read().strip()
        self.assertEqual(actual_content.strip(), expected_content)

if __name__ == "__main__":
    unittest.main()
