import json
import os
import unittest
from unittest.mock import patch, Mock

from src.lib.topic_discovery import discover_topic
from src.lib.models_discovery import PreviewResult

class TestTopicDiscovery(unittest.TestCase):
    def test_discover_topic_empty(self):
        result = discover_topic("富士山", limit=10)
        self.assertIsInstance(result, PreviewResult)
        self.assertEqual(result.total_images, 0)
        self.assertEqual(result.query_log.topic, "富士山")

    @patch("src.lib.topic_discovery.logger")
    def test_logging_called(self, mock_logger):
        _ = discover_topic("桜")
        # Ensure start/end logs invoked
        calls = [c.args for c in mock_logger.info.call_args_list]
        start = any("discover_topic.start" in (args[0] if args else "") for args in calls)
        end = any("discover_topic.end" in (args[0] if args else "") for args in calls)
        self.assertTrue(start and end)

if __name__ == "__main__":
    unittest.main()
