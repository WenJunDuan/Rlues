"""Rule hasher skeleton with unified response envelope."""


def hash_rules(skill_dir: str) -> dict:
    return {
        "ok": False,
        "code": "NOT_IMPLEMENTED",
        "message": "rule_hasher.hash_rules not implemented",
        "data": {"skill_dir": skill_dir, "rules": []},
        "meta": {"plugin": "rule_hasher"},
    }
