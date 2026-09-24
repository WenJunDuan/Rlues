"""Business contract regressions against the actual 9.9.9 packages."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[6]
PACKAGES = [ROOT / f"vibeCoding/old/04-athena-8.9-9.9.9/{vendor}/9.9.9/.{platform}" for vendor, platform in (("claude", "claude"), ("codex", "codex"))]


def load(path: Path):
    spec = importlib.util.spec_from_file_location("contract_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capability_manifest():
    return {
        "schema": "project-capability-manifest", "version": 1,
        "service": "test-business", "transport": "stdio", "endpoint": "test-reader",
        "auth": {"type": "preauthorized"}, "identity": {"passthrough": True},
        "capabilities": [{"name": "request.read", "mode": "read", "tool": "readRequest",
            "permission": "request:read", "data_scope": "target-enforced", "audit": True,
            "redaction": [], "input_schema": {"type": "object"}, "output_schema": {"type": "object"}}],
    }


class FullstackContractTests(unittest.TestCase):
    def test_business_contract_accepts_current_resources(self):
        for package in PACKAGES:
            with self.subTest(package=package.name):
                skill = package / "skills/biz-delivery-loop"
                errors, _ = load(skill / "scripts/check_delivery_loop_contract.py").validate(skill)
                self.assertEqual(errors, [])

    def test_three_review_artifacts_cannot_reenter_business_workflow(self):
        for package in PACKAGES:
            with self.subTest(package=package.name), tempfile.TemporaryDirectory() as tmp:
                source = package / "skills/biz-delivery-loop"
                skill = Path(tmp) / "biz"
                shutil.copytree(source, skill)
                with (skill / "SKILL.md").open("a") as handle:
                    handle.write("\n交付必须先生成 reviews/pass1.md、reviews/pass2.md、reviews/pass3.md。\n")
                errors, _ = load(source / "scripts/check_delivery_loop_contract.py").validate(skill)
                self.assertTrue(any("review" in error.lower() for error in errors), errors)

    def test_readonly_data_contract_rejects_write_secrets_and_missing_scope(self):
        for package in PACKAGES:
            validator = load(package / "skills/quantum-data/scripts/check_capability_manifest.py")
            good = capability_manifest()
            self.assertEqual(validator.validate(good)[0], [])
            write = copy.deepcopy(good)
            write["capabilities"][0]["mode"] = "write"
            secret = copy.deepcopy(good)
            secret["auth"]["access_token"] = "fixture-value"
            unscoped = copy.deepcopy(good)
            del unscoped["capabilities"][0]["data_scope"]
            for bad in (write, secret, unscoped):
                with self.subTest(package=package.name, bad=bad):
                    self.assertTrue(validator.validate(bad)[0])

    def test_manifest_cli_rejects_malformed_input(self):
        for package in PACKAGES:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "invalid.json"
                path.write_text('{"schema":')
                result = subprocess.run([sys.executable, str(package / "skills/quantum-data/scripts/check_capability_manifest.py"), str(path)], capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["status"], "fail")


if __name__ == "__main__":
    unittest.main()
