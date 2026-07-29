"""Contract tests for the global model-registry builder."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODELS_TEMPLATE = ROOT / "templates" / "commands" / "models.md"
IMPLEMENT_TEMPLATE = ROOT / "templates" / "commands" / "implement.md"


def _models_content() -> str:
    return MODELS_TEMPLATE.read_text(encoding="utf-8")


def test_models_command_builds_the_three_global_catalogs():
    content = _models_content()

    assert "global registry at `~/.specify/models.json`" in content
    assert "Always write the global file `~/.specify/models.json`" in content
    assert "Do not create a" in content
    assert "project-local `.specify/models.json`" in content
    assert '"version": 2' in content
    assert '"models"' in content
    assert '"clis"' in content
    assert '"commands"' in content


def test_models_command_asks_which_clis_to_integrate():
    content = _models_content()

    assert "ask the user which detected CLIs to integrate" in content
    assert "selecting one or more detected CLIs" in content
    assert "entering an executable name or absolute path" in content
    assert "Do not automatically integrate every detected executable" in content


def test_models_command_is_not_bound_to_a_static_cli_or_model_catalog():
    content = _models_content()

    assert "must not contain or rely on" in content
    assert "built-in catalog of CLI names, model names, model aliases" in content
    assert "Do not maintain a static alias" in content
    assert "table in this command" in content
    assert "__SPECKIT_EXECUTOR_BLOCK__" not in content
    assert "subagent_type" not in content
    assert "hermes chat" not in content


def test_models_command_accepts_models_the_cli_does_not_display():
    content = _models_content()

    assert "models that the selected CLI does not" in content
    assert "display but can execute" in content
    assert "Do you want to add any model that this CLI does not display" in content
    assert "Treat those models exactly like displayed models" in content
    assert "must not label it as hidden" in content


def test_models_command_collects_effective_context_and_effort_per_cli_model():
    content = _models_content()

    assert '"context_window": 0' in content
    assert '"effort_levels": ["<exact-effort-value>"]' in content
    assert "effective CLI context window wins" in content
    assert "positive integer token count" in content


def test_models_command_requires_complete_openrouter_description():
    content = _models_content()

    assert "https://openrouter.ai/api/v1/models" in content
    assert "https://openrouter.ai/api/frontend/v1/rankings/benchmarks" in content
    assert "https://openrouter.ai/api/frontend/v1/rankings/performance" in content
    assert '"intelligence"' in content
    assert '"speed"' in content
    assert '"input_per_million"' in content
    assert '"output_per_million"' in content
    assert '"benefits"' in content
    assert "Never persist an incomplete model" in content


def test_models_command_asks_for_help_when_official_information_is_missing():
    content = _models_content()

    assert "official sites do not explain how the CLI is" in content
    assert "administered" in content
    assert "ask whether the user can provide a reference" in content
    assert "Do not improvise vendor-specific flags" in content
    assert "If the data still cannot be completed, do not add or update that model" in content


def test_models_command_writes_structured_execution_recipes():
    content = _models_content()

    assert '"executable"' in content
    assert '"argv"' in content
    assert '"transport": "stdin | argument | file"' in content
    assert '"mode": "argument | config | fixed | unsupported"' in content
    assert '"mode": "argument | config | fixed | automatic"' in content
    assert '"working_directory": "{project_root}"' in content
    assert "Never store a shell command string" in content


def test_models_command_tests_recipes_but_does_not_persist_status_or_provenance():
    content = _models_content()

    assert "Test before writing" in content
    assert "Confirm model selection, effort values, and context behavior" in content
    assert "ask the user for approval" in content
    assert 'Do not write `verified`, `status`' in content
    assert '"verified"' not in content
    assert '"status"' not in content
    assert '"discovery"' not in content
    assert '"source"' not in content


def test_models_command_updates_incrementally_and_requires_confirmation():
    content = _models_content()

    assert "The command is incremental" in content
    assert "Preserve integrations the user does not select" in content
    assert "Ask the user to confirm the final update" in content
    assert "Write atomically" in content


def test_models_command_has_no_legacy_routing_schema():
    content = _models_content()

    assert "does **not** choose a manager" in content
    assert "assign implementation tasks" in content
    assert "difficulty" not in content.lower()
    assert '  "manager":' not in content
    assert '"by_complexity"' not in content
    assert '"executors"' not in content


def test_models_command_assigns_only_eligible_commands():
    content = _models_content()

    for command in (
        "constitution",
        "specify",
        "clarify",
        "plan",
        "checklist",
        "tasks",
        "analyze",
        "taskstoissues",
        "converge",
    ):
        assert f"`{command}`" in content

    assert "Never add a" in content
    assert "command assignment for `models`, `implement`, `flow-quick`, or `flow-full`" in content
    assert "contains exactly the nine eligible command keys" in content


def test_models_command_recommends_but_user_decides_assignments():
    content = _models_content()

    assert "Recommend one default combination" in content
    assert "Ask the user to accept the recommendation" in content
    assert "Allow the user to accept all recommendations together" in content
    assert "Never save a recommendation as a decision before the user" in content
    assert "Recommendations are advisory" in content


def test_models_command_records_default_and_ordered_alternatives():
    content = _models_content()

    assert "index `0` is the default executor" in content
    assert "index `1` and later are alternatives tried in order" in content
    assert "array order is not load balancing" in content
    assert '"cli": "<cli-key>"' in content
    assert '"model": "<canonical-model-id>"' in content
    assert '"effort": "<exact-effort-value-or-null>"' in content
    assert '"context_window": 0' in content


def test_models_command_validates_each_command_executor_combination():
    content = _models_content()

    assert "references an existing canonical model and CLI" in content
    assert "availability entry for the referenced CLI" in content
    assert "effort is listed in that availability" in content
    assert "does not exceed the effective" in content
    assert "canonical model key, not the CLI-specific model string" in content


def test_models_command_renders_identically_for_every_integration():
    """The builder learns selected CLIs at runtime instead of receiving an
    executor block from the integration that installed the command."""
    from specify_cli.integrations import INTEGRATION_REGISTRY

    raw = _models_content()
    rendered = set()
    for key, integration in INTEGRATION_REGISTRY.items():
        output = integration.process_template(
            raw,
            key,
            "sh",
            "$ARGUMENTS",
        )
        assert "__SPECKIT_EXECUTOR_BLOCK__" not in output, key
        rendered.add(output)

    assert len(rendered) == 1


def test_eligible_commands_use_their_preassigned_executor():
    commands_dir = ROOT / "templates" / "commands"
    eligible = (
        "constitution",
        "specify",
        "clarify",
        "plan",
        "checklist",
        "tasks",
        "analyze",
        "taskstoissues",
        "converge",
    )

    for command in eligible:
        template = commands_dir / f"{command}.md"
        content = template.read_text(encoding="utf-8")
        marker = f"__SPECKIT_ASSIGNED_COMMAND_BLOCK_{command.upper()}__"
        assert marker in content, template.name
        assert "## Command Workflow" in content, template.name
        assert "Predefined command difficulty" not in content, template.name
        assert "Model configuration gate" not in content, template.name
        assert "Orchestrator dispatch (MANDATORY" not in content, template.name
        assert "by_complexity" not in content, template.name
        assert "__SPECKIT_DISPATCH_BLOCK__" not in content, template.name
        assert "subagent_type" not in content, template.name

    models_content = _models_content()
    assert "Read the command's purpose, workflow" in models_content
    assert "difficulty" not in models_content.lower()


def test_tasks_preassigns_each_implementation_executor():
    content = (ROOT / "templates" / "commands" / "tasks.md").read_text(
        encoding="utf-8"
    )
    task_template = (ROOT / "templates" / "tasks-template.md").read_text(
        encoding="utf-8"
    )

    assert (
        "[E:cli=<cli>|model=<model>|effort=<effort>|context=<tokens>]"
        in content
    )
    assert "Do not omit fields" in content
    assert "do not defer executor selection" in content
    assert "canonical model key from `models`" in content
    assert "availability entry for the selected CLI" in content
    assert "by_complexity" not in content
    assert "difficulty" not in content.lower()
    assert (
        "[E:cli=<cli>|model=<model>|effort=<effort>|context=<tokens>]"
        in task_template
    )
    assert "by_complexity" not in task_template
    assert "[C:" not in task_template
    assert "difficulty" not in task_template.lower()


def test_implement_uses_exact_task_executor_assignments():
    content = IMPLEMENT_TEMPLATE.read_text(encoding="utf-8")

    assert "Global executor registry" in content
    assert "Require valid JSON with `version: 2`" in content
    assert "[E:cli=<cli>|model=<model>|effort=<effort>|context=<tokens>]" in content
    assert "MUST NOT classify a task" in content
    assert "Never apply a default executor" in content
    assert "Find the label's canonical `model`" in content
    assert "Do not silently" in content
    assert "choose another CLI or model" in content
    assert "parallelize ready [P] tasks" in content
    assert "launching each task's assigned CLI" in content
    assert "by_complexity" not in content
    assert "__SPECKIT_DISPATCH_BLOCK__" not in content
    assert "[C:" not in content
