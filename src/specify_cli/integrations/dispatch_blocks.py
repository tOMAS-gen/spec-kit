"""Global command-executor block rendering."""

from __future__ import annotations

import re

# Runtime-learned command executor. This block is identical for every
# integration: models.json supplies the CLI recipe, model, effort, and context
# window.
ASSIGNED_COMMAND_PLACEHOLDER_RE = re.compile(
    r"__SPECKIT_ASSIGNED_COMMAND_BLOCK_([A-Z0-9-]+)__"
)
TASK_INTERACTION_PLACEHOLDER = "__SPECKIT_TASK_INTERACTION_BLOCK__"

DELEGATED_INTERACTION_PROTOCOL = """\
## Delegated User Interaction and Resume Protocol (MANDATORY)

The principal CLI owns every conversation with the user. A delegated worker
must never wait on its own terminal, invent an answer, or treat a question as a
failure.

### Durable run state

Before launching a worker, the principal CLI must:

1. Inspect `.specify/orchestration/runs/` for a non-terminal run matching the
   same command or task ID and executor assignment. If one exists, offer to
   resume it instead of creating another run. Never execute the same paused
   work twice.
2. Generate a filesystem-safe unique `run_id` only when no run is resumed.
3. Ensure `.specify/orchestration/.gitignore` excludes all runtime contents
   except that `.gitignore` itself. Never stage a run directory.
4. Create `.specify/orchestration/runs/<run_id>/`.
5. Atomically write `state.json` with permissions restricted to the current
   user when the platform supports it.
6. Record:
   - `version: 1`, `run_id`, and `kind` (`command` or `task`);
   - command name and optional task ID;
   - `status: "running"`;
   - the exact CLI, canonical model, CLI-specific model ID, effort, and context;
   - session mode and a null session ID until one is captured;
   - empty checkpoint, questions, and answers arrays.

Runtime state belongs in this project-local run directory, never in the global
model registry. Write every state transition atomically. Do not persist API
keys, authorization values, passwords, or other secrets.

### Worker pause contract

The worker receives `run_id`, the absolute run directory, and this complete
protocol in its prompt. When it needs user input, it must:

1. Reach a safe boundary and stop before any action that depends on the answer.
2. Update `state.json` with:
   - `status: "awaiting_user_input"`;
   - the captured native session ID when available;
   - completed steps and the current step;
   - pending work and dependencies;
   - changed files and validation results;
   - one or more questions with stable IDs, context, and options when useful.
3. Preserve enough information to avoid repeating completed side effects.
4. Atomically save the state, print
   `SPECKIT_CONTROL awaiting_user_input <run_id>`, and exit cleanly.

The worker must not ask the user directly or remain blocked waiting for stdin.
As soon as CLI output exposes a native session ID, the principal must extract
it using `execution.session.capture` and atomically persist it in `state.json`.

### Principal question and resume contract

When the principal sees the control line or an `awaiting_user_input` state:

1. Treat it as a pause, not a failure. Never select a fallback executor.
2. Ask the recorded questions in the principal conversation and wait.
3. Store answers by question ID, set `status: "resuming"`, and save atomically.
   If an answer contains a secret, pass it only through the resumed process'
   input and persist a redacted marker instead of the secret.
4. Resume the exact same CLI, model, effort, and context:
   - For `session.mode: "native"`, require the captured session ID and render
     the CLI's `session.resume` recipe with `{session_id}`, the original
     assignment placeholders, and the answer text.
   - For `session.mode: "checkpoint"`, launch a new process using the original
     execution recipe and a continuation prompt containing the checkpoint,
     pending questions, and answers. This is continuation on the same assigned
     executor, not a restart or fallback.
5. Tell the resumed worker to load `state.json`, continue from the recorded
   step, and not repeat completed work.
6. Repeat the pause/resume cycle as often as needed. On success set
   `status: "completed"`; on a real execution failure set `status: "failed"`
   and preserve the checkpoint for diagnosis.

A timeout while awaiting the user's answer is not an executor failure. Keep the
run resumable. Do not advance a dependent command or task until the paused run
completes.
"""

ASSIGNED_COMMAND_BLOCK = """\
## Assigned Command Execution (MANDATORY)

This wrapper runs in the CLI that received the command. It must delegate the
entire command workflow to the executor assigned to `__COMMAND__`; it must not
perform the workflow itself.

1. Read `~/.specify/models.json`. Do not read a project-local models file.
   Require valid JSON with `version: 3` and non-empty `models`, `clis`, and
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
     `{effort}`, `{context_window}`, `{project_root}`, `{run_id}`, and
     `{run_dir}` as specified by that recipe. Keep argv as an argument array;
     never evaluate a shell string.
   - Require a valid `execution.session` recipe. Use native session capture and
     resume when its mode is `native`; otherwise use checkpoint continuation.
   - Build the worker text from the original user input plus every instruction
     under `## Command Workflow`. Include the line
     `ASSIGNED_COMMAND_WORKER: __COMMAND__` and tell the worker to execute that
     workflow directly, without running this wrapper or delegating the whole
     command again. Include the workflow requirements and the complete
     delegated user-interaction protocol in full.
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
""" + "\n" + DELEGATED_INTERACTION_PROTOCOL


def resolve_assigned_command_blocks(content: str) -> str:
    """Render runtime-learned command executor placeholders."""

    content = ASSIGNED_COMMAND_PLACEHOLDER_RE.sub(
        lambda match: ASSIGNED_COMMAND_BLOCK.replace(
            "__COMMAND__", match.group(1).lower()
        ),
        content,
    )
    return content.replace(TASK_INTERACTION_PLACEHOLDER, DELEGATED_INTERACTION_PROTOCOL)
