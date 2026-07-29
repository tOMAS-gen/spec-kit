"""Global command-executor block rendering."""

from __future__ import annotations

import re

# Runtime-learned command executor. This block is identical for every
# integration: models.json supplies the CLI recipe, model, effort, and context
# window.
ASSIGNED_COMMAND_PLACEHOLDER_RE = re.compile(
    r"__SPECKIT_ASSIGNED_COMMAND_BLOCK_([A-Z0-9-]+)__"
)

ASSIGNED_COMMAND_BLOCK = """\
## Assigned Command Execution (MANDATORY)

This wrapper runs in the CLI that received the command. It must delegate the
entire command workflow to the executor assigned to `__COMMAND__`; it must not
perform the workflow itself.

1. Read `~/.specify/models.json`. Do not read a project-local models file.
   Require valid JSON with `version: 2` and non-empty `models`, `clis`, and
   `commands` arrays. If it is missing or invalid, STOP and tell the user to run
   `__SPECKIT_COMMAND_MODELS__`.
2. Find the single `commands` entry keyed by `__COMMAND__`. Require a non-empty
   ordered array. Index `0` is the default; later entries are alternatives.
3. For each combination in order:
   - Resolve its canonical `model` in `models` and its `cli` in `clis`.
   - Find the model availability whose `cli` matches the combination and use
     that availability's exact CLI-specific model ID.
   - Validate that the assigned `effort` is supported (or is `null` only when
     effort is unsupported) and that assigned `context_window` is positive and
     no larger than the availability limit.
   - Load the CLI's structured execution recipe. Substitute `{model}`,
     `{effort}`, `{context_window}`, and `{project_root}` as specified by that
     recipe. Keep argv as an argument array; never evaluate a shell string.
   - Build the worker text from the original user input plus every instruction
     under `## Command Workflow`. Include the line
     `ASSIGNED_COMMAND_WORKER: __COMMAND__` and tell the worker to execute that
     workflow directly, without running this wrapper or delegating the whole
     command again. Include the workflow requirements in full rather than
     summarizing away normative instructions.
   - Deliver the text using the recipe's `stdin`, `argument`, or `file`
     transport and launch the executable in `{project_root}`. Apply the recorded
     effort and context mechanisms exactly as specified by the recipe.
   - Wait for the worker to finish and capture its output and exit status.
4. Use the next combination only when the current CLI/model cannot be invoked,
   is unavailable, rejects the assigned model/effort/context, is rate-limited,
   lacks quota, or cannot fit the command envelope. Announce:
   `COMMAND EXECUTOR __COMMAND__: <cli> / <model>`, including `fallback <n>`
   for alternatives.
5. Once a worker begins substantive workflow actions, do not blindly restart
   the whole command with another executor. Return its result or report its
   workflow failure with the preserved state so completed side effects are not
   duplicated.
6. When one worker completes successfully, relay its result and STOP. The
   receiving CLI must not execute `## Command Workflow` a second time. If every
   combination is exhausted, report each attempted CLI/model and failure, then
   STOP.
"""


def resolve_assigned_command_blocks(content: str) -> str:
    """Render runtime-learned command executor placeholders."""

    return ASSIGNED_COMMAND_PLACEHOLDER_RE.sub(
        lambda match: ASSIGNED_COMMAND_BLOCK.replace(
            "__COMMAND__", match.group(1).lower()
        ),
        content,
    )
