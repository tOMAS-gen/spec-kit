"""opencode integration."""

from ..base import MarkdownIntegration


class OpencodeIntegration(MarkdownIntegration):
    key = "opencode"
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        # opencode loads commands from `command/` (singular). A plural
        # `commands/` directory is silently ignored, so the commands install
        # but never appear in the CLI.
        "commands_subdir": "command",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/command",
        "legacy_dir": ".opencode/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        args = [self._resolve_executable(), "run"]
        # Apply operator-injected extra args before the prompt-derived
        # --command and the canonical --format/-m flags so Spec Kit's
        # later appends remain authoritative under repeated-flag CLI
        # semantics.
        self._apply_extra_args_env_var(args)

        message = prompt
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["--command", command])
                message = remainder

        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--format", "json"])
        if message:
            args.append(message)
        return args
