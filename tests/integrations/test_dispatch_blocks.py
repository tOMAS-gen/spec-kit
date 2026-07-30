"""Tests for global command-executor block injection."""

from pathlib import Path

import pytest

from specify_cli.integrations import INTEGRATION_REGISTRY
from specify_cli.integrations.dispatch_blocks import (
    ASSIGNED_COMMAND_PLACEHOLDER_RE,
    TASK_INTERACTION_PLACEHOLDER,
)

ROOT = Path(__file__).resolve().parents[2]
COMMANDS_DIR = ROOT / "templates" / "commands"
ASSIGNED_COMMANDS = {
    "constitution",
    "specify",
    "clarify",
    "plan",
    "checklist",
    "tasks",
    "analyze",
    "taskstoissues",
    "converge",
}


def test_core_templates_have_no_legacy_dispatch_placeholders():
    for template in COMMANDS_DIR.glob("*.md"):
        content = template.read_text(encoding="utf-8")
        assert "__SPECKIT_DISPATCH_BLOCK__" not in content, template.name
        assert "__SPECKIT_EXECUTOR_BLOCK__" not in content, template.name


def test_assigned_commands_use_the_global_registry_placeholder():
    for command in ASSIGNED_COMMANDS:
        content = (COMMANDS_DIR / f"{command}.md").read_text(encoding="utf-8")
        placeholders = ASSIGNED_COMMAND_PLACEHOLDER_RE.findall(content)
        assert placeholders == [command.upper()], command
        assert "## Command Workflow" in content
        assert "Model configuration gate" not in content
        assert "by_complexity" not in content
        assert "difficulty level" not in content.lower()


def test_assigned_command_render_is_cli_neutral():
    raw = (COMMANDS_DIR / "specify.md").read_text(encoding="utf-8")
    for key, integration in INTEGRATION_REGISTRY.items():
        output = integration.process_template(
            raw,
            key,
            "sh",
            "$ARGUMENTS",
        )
        assert not ASSIGNED_COMMAND_PLACEHOLDER_RE.search(output), key
        assert "commands` entry keyed by `specify`" in output, key
        assert "ASSIGNED_COMMAND_WORKER: specify" in output, key
        assert "Delegated User Interaction and Resume Protocol" in output, key
        assert ".specify/orchestration/runs/<run_id>/" in output, key
        assert ".specify/orchestration/.gitignore" in output, key
        assert "Never stage a run directory" in output, key
        assert "offer to" in output, key
        assert "resume it instead of creating another run" in output, key
        assert "SPECKIT_CONTROL awaiting_user_input <run_id>" in output, key
        assert "principal must extract" in output, key
        assert "`execution.session.capture`" in output, key
        assert "Never select a fallback executor" in output, key
        assert "session.mode: \"native\"" in output, key
        assert "session.mode: \"checkpoint\"" in output, key
        assert "subagent_type" not in output, key
        assert "hermes chat" not in output, key


def test_implement_renders_the_same_task_interaction_protocol():
    raw = (COMMANDS_DIR / "implement.md").read_text(encoding="utf-8")
    output = INTEGRATION_REGISTRY["generic"].process_template(
        raw,
        "generic",
        "sh",
        "$ARGUMENTS",
    )

    assert TASK_INTERACTION_PLACEHOLDER not in output
    assert "Delegated User Interaction and Resume Protocol" in output
    assert "status: \"awaiting_user_input\"" in output
    assert "same CLI, model, effort, and context" in output


@pytest.mark.parametrize("key", ["hermes", "opencode"])
def test_installed_commands_use_global_assignments(key, tmp_path, monkeypatch):
    """Installed commands resolve executors from the same global registry."""
    from specify_cli.integrations.manifest import IntegrationManifest

    project = tmp_path / "proj"
    project.mkdir()
    # Hermes installs to ~/.hermes/skills (global) — redirect HOME so the test
    # never touches the real user directory.
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))

    integ = INTEGRATION_REGISTRY[key]
    manifest = IntegrationManifest(integ.key, project.resolve())
    created = integ.setup(project, manifest, script_type="sh")

    workflow = [p for p in created if "models" not in Path(p).stem.lower()
                and "models" not in Path(p).parent.name.lower()]
    blob = "\n".join(Path(p).read_text(encoding="utf-8") for p in workflow)
    assert "ASSIGNED_COMMAND_WORKER: specify" in blob
    assert "__SPECKIT_ASSIGNED_COMMAND_BLOCK_" not in blob
    assert "by_complexity" not in blob
    assert "DISPATCH n<level>" not in blob
    assert "subagent_type" not in blob
