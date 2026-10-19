import pytest

from app.simulation.apl_mutator import build_priority_apl, sanitize_skip_actions, validate_custom_apl


def test_sanitize_skip_actions() -> None:
    assert sanitize_skip_actions(["Recklessness", "avatar", "avatar"]) == "recklessness/avatar"


def test_reject_bad_skip_token() -> None:
    with pytest.raises(ValueError):
        sanitize_skip_actions(["rm -rf /"])


def test_validate_custom_apl_allows_actions() -> None:
    lines = validate_custom_apl("actions=auto_attack\nactions+=/bloodthirst\n")
    assert lines[0].startswith("actions=")


def test_validate_custom_apl_forbids_threads() -> None:
    with pytest.raises(ValueError):
        validate_custom_apl("threads=64")


def test_build_priority_apl() -> None:
    lines = build_priority_apl(["bloodthirst", "rampage"])
    assert lines[0] == "actions=auto_attack"
    assert "actions+=/bloodthirst" in lines
