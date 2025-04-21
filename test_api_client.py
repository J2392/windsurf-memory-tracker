import unittest
from api_client import WindSurfAPIClient

class TestAPIClient(unittest.TestCase):
    def test_event_callback(self):
        events = []
        def cb(event):
            events.append(event)
        client = WindSurfAPIClient(on_event_callback=cb, poll_interval=1)
        client._generate_mock_event = lambda: {'type': 'test', 'data': 123}
        client.running = True
        client._mock_event_listener()
        import time
        time.sleep(2)
        client.running = False
        self.assertTrue(any(e['type'] == 'test' for e in events))

if __name__ == "__main__":
    unittest.main()
