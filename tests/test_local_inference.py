"""Exercise both HTTP contracts against a real local fixture server."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from anima.llm import LocalHTTP, Ollama


class InferenceContractTest(unittest.TestCase):
    def test_local_generation_uses_separate_embedding_lane(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.respond({"data": [{"id": "fixture-model"}]})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, body))
                if self.path == "/v1/chat/completions":
                    self.respond({"model": "fixture-model", "choices": [{
                        "message": {"content": '{"thought":"Observe the sky"}'},
                        "finish_reason": "stop"}], "usage": {"completion_tokens": 8}})
                elif self.path == "/api/chat":
                    self.respond({"model": "fixture-model", "message": {"content": '{"ok":true}'},
                                  "eval_count": 4})
                else:
                    self.respond({"embeddings": [[0.25, 0.75]]})

            def respond(self, data):
                raw = json.dumps(data).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            ollama = Ollama(url, "fixture-model", "embed-fixture", keep_alive="-1", think=False)
            local = LocalHTTP(url + "/v1", "fixture-model", ollama)
            self.assertTrue(local.alive())
            self.assertEqual(local.chat_json("JSON only", "Continue")["thought"], "Observe the sky")
            self.assertEqual(local.embed("Sky"), [0.25, 0.75])
            self.assertEqual(ollama.chat_json("JSON only", "Test"), {"ok": True})
            self.assertEqual(requests[0][0], "/v1/chat/completions")
            self.assertIs(requests[0][1]["chat_template_kwargs"]["enable_thinking"], False)
            self.assertEqual(requests[1][1]["model"], "embed-fixture")
            self.assertEqual(requests[1][1]["keep_alive"], -1)
            self.assertEqual(requests[2][1]["keep_alive"], -1)
            self.assertIs(requests[2][1]["think"], False)
            self.assertEqual(len(local.last_generation["json_attempts"]), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
