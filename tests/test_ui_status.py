"""Completed bounded runs must not appear alive during the freshness window."""
import contextlib
import io
import json
import tempfile
import time
import unittest

from anima.__main__ import cmd_status
from anima.config import Config
from anima.server import Api


class StatusTest(unittest.TestCase):
    def test_completed_run_is_stopped_in_both_interfaces(self):
        with tempfile.TemporaryDirectory() as root:
            cfg = Config(runtime_dir=root)
            api = Api(cfg)
            for phase, expected in (("awake", True), ("stopped", False)):
                cfg.state_path.write_text(json.dumps({"ts": time.time(), "phase": phase}))
                self.assertEqual(api.state()["daemon_alive"], expected)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    cmd_status(cfg, None)
                self.assertEqual(json.loads(output.getvalue())["daemon_looks_alive"], expected)


if __name__ == "__main__":
    unittest.main()
