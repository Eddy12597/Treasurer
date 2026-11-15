import unittest
from unittest.mock import patch

from flask import Flask

import app as treasurer_app
from app import rate_limit


class RateLimitTests(unittest.TestCase):
    def make_client(self, max_requests=2, window_seconds=60):
        app = Flask(__name__)

        @app.get("/")
        @rate_limit(max_requests, window_seconds)
        def endpoint():
            return {"ok": True}

        return app.test_client()

    def test_rejects_excess_requests_with_retry_headers(self):
        client = self.make_client()

        first = client.get("/", environ_base={"REMOTE_ADDR": "192.0.2.1"})
        second = client.get("/", environ_base={"REMOTE_ADDR": "192.0.2.1"})
        third = client.get("/", environ_base={"REMOTE_ADDR": "192.0.2.1"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers["X-RateLimit-Remaining"], "1")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.headers["X-RateLimit-Remaining"], "0")
        self.assertEqual(third.status_code, 429)
        self.assertEqual(third.get_json(), {"error": "Rate limit exceeded"})
        self.assertEqual(third.headers["X-RateLimit-Limit"], "2")
        self.assertEqual(third.headers["X-RateLimit-Remaining"], "0")
        self.assertGreaterEqual(int(third.headers["Retry-After"]), 1)

    def test_tracks_each_client_separately(self):
        client = self.make_client(max_requests=1)

        first = client.get("/", environ_base={"REMOTE_ADDR": "192.0.2.1"})
        second = client.get("/", environ_base={"REMOTE_ADDR": "192.0.2.2"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

    def test_api_logs_route_uses_the_rate_limit(self):
        remote_addr = "198.51.100.10"
        with patch.object(treasurer_app, "get_logs", return_value=({"data": []}, 200)) as get_logs:
            client = treasurer_app.app.test_client()
            responses = [
                client.get("/api/logs", environ_base={"REMOTE_ADDR": remote_addr})
                for _ in range(61)
            ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:60]))
        self.assertEqual(responses[60].status_code, 429)
        self.assertEqual(get_logs.call_count, 60)

    def test_allows_requests_after_the_window_expires(self):
        client = self.make_client(max_requests=1, window_seconds=10)

        with patch("app.time.monotonic", side_effect=[100.0, 111.0]):
            first = client.get("/", environ_base={"REMOTE_ADDR": "192.0.2.1"})
            second = client.get("/", environ_base={"REMOTE_ADDR": "192.0.2.1"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)


if __name__ == "__main__":
    unittest.main()
