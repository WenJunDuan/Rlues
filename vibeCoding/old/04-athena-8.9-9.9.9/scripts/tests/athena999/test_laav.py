"""Offline LLM-as-a-Verifier scoring regressions. No network."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[6]
RANK = ROOT / "vibeCoding/old/04-athena-8.9-9.9.9/claude/9.9.9/.claude/skills/llm-as-a-verifier/scripts/rank.py"


def load_rank():
    spec = importlib.util.spec_from_file_location("athena_laav_rank", RANK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LaavScoring(unittest.TestCase):
    def setUp(self):
        self.rank = load_rank()

    def test_missing_top_logprobs_is_unscored(self):
        score, token = self.rank.expected_score(
            {"content": [{"token": "SCORE="}, {"token": "12", "top_logprobs": []}]}
        )
        self.assertIsNone(score)
        self.assertIsNone(token)

    def test_split_integer_tokens_are_not_discrete_fallback(self):
        score, token = self.rank.expected_score(
            {
                "content": [
                    {"token": "SCORE="},
                    {"token": "2", "top_logprobs": [{"token": "2", "logprob": -0.1}]},
                    {"token": "0", "top_logprobs": [{"token": "0", "logprob": -0.1}]},
                ]
            }
        )
        self.assertIsNone(score)
        self.assertIsNone(token)

    def test_all_unscorable_candidates_skip_not_ranked(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "packet.md").write_text("AC1: correct behavior\n")
            for name in ("a.diff", "b.diff"):
                (base / name).write_text("candidate\n")
            os.environ["ATHENA_LAAV_FORCE"] = "1"
            os.environ["ATHENA_LAAV_BASE_URL"] = "https://example.invalid/v1"
            os.environ["ATHENA_LAAV_API_KEY"] = "fixture-key-never-transmitted"
            self.rank.complete = lambda *args: {
                "choices": [{"logprobs": {"content": [{"token": "unknown", "top_logprobs": []}]}}]
            }
            output = base / "result.json"
            sys.argv = [
                "rank.py",
                "--packet",
                str(base / "packet.md"),
                "--candidate",
                str(base / "a.diff"),
                "--candidate",
                str(base / "b.diff"),
                "--output",
                str(output),
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                code = self.rank.main()
            payload = json.loads(output.read_text())
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "skipped")
            self.assertEqual(payload["reason"], "logprobs_unavailable")
            self.assertTrue(all(row["expected_score"] is None for row in payload["ranked"]))


if __name__ == "__main__":
    unittest.main()
