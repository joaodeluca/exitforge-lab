from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import sys
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from http_adapter import MAX_BYTES, Refused, get_json, resolve_pinned
from live_demo import fetch_and_aggregate


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/timeout":
            time.sleep(0.2)
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://metadata.google.internal/")
            self.end_headers()
            return
        body = json.dumps({"fixture": True, "path": self.path}).encode()
        if self.path == "/large":
            body = b"x" * (MAX_BYTES + 1)
        elif self.path == "/invalid":
            body = b"{invalid"
        self.send_response(500 if self.path == "/failure" else 200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class HttpAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_real_loopback_gets_preserve_objects_and_tag_without_partial_output(self):
        result = fetch_and_aggregate(self.base + "/traffic", self.base + "/revenue", allow_loopback=True)
        self.assertEqual("completed_public_get", result["result"]["status"])
        self.assertEqual(2, result["result"]["network_calls"])
        self.assertEqual(["/traffic", "/revenue"], [item["path"] for item in result["result"]["items"]])
        self.assertTrue(all(item["report_type"] == "daily-kpi" for item in result["result"]["items"]))
        self.assertTrue(all(event["body_sha256"] for event in result["source_events"]))

    def test_http500_is_failure_and_suppresses_successful_peer(self):
        result = fetch_and_aggregate(self.base + "/ok", self.base + "/failure", allow_loopback=True)
        self.assertEqual("failed", result["result"]["status"])
        self.assertEqual([], result["result"]["items"])
        self.assertEqual("HTTP_500", result["source_events"][1]["error"])

    def test_timeout_is_unknown_not_success(self):
        result = fetch_and_aggregate(self.base + "/ok", self.base + "/timeout", timeout=0.05, allow_loopback=True)
        self.assertEqual("unknown", result["result"]["status"])
        self.assertEqual([], result["result"]["items"])
        self.assertEqual("TIMEOUT", result["source_events"][1]["error"])

    def test_refuses_scheme_private_metadata_userinfo_and_default_loopback(self):
        urls = ["file:///etc/passwd", "http://example.com/", "https://10.0.0.1/", "https://169.254.169.254/", "https://224.0.0.1/", "https://[fec0::1]/", "https://[::ffff:127.0.0.1]/", "https://metadata.google.internal/", "https://user:secret@example.com/", "https://example.com/?token=value", self.base + "/ok"]
        for url in urls:
            with self.subTest(url=url):
                with patch("socket.getaddrinfo", side_effect=AssertionError("refusal must precede DNS")):
                    event = get_json(url)
                self.assertEqual("failed", event["status"])
                self.assertEqual(0, event["request_count"])

    def test_refuses_private_dns_even_with_loopback_flag(self):
        answers = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch("socket.getaddrinfo", return_value=answers):
            with self.assertRaises(Refused):
                resolve_pinned("example.com", 443, 1, True)

    def test_redirect_body_limit_and_invalid_json_are_refused(self):
        expected = {"/redirect": "REDIRECT_FORBIDDEN", "/large": "BODY_LIMIT_OR_INVALID_LENGTH", "/invalid": "JSONDecodeError"}
        for path, code in expected.items():
            with self.subTest(path=path):
                event = get_json(self.base + path, allow_loopback=True)
                self.assertEqual("failed", event["status"])
                self.assertEqual(code, event["error"])
                self.assertEqual(1, event["request_count"])


if __name__ == "__main__":
    unittest.main()
