---
description: Run the short Spec Kit flow end-to-end (specify → plan → tasks → implement → converge) with a single stop before implementation.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Flag parsing**: extract flags from the user input before using the rest as the feature description:

- `--bypass` — skip the implementation gate ONLY (no stop before implement). It does NOT suppress user questions: every phase still asks the user whatever it needs.
- `--loop` — after implementing, loop implement ↔ converge until converged (max 5 iterations). Without it, converge runs exactly once.
- Everything else in the input is the **feature description** passed to the specify phase. If the description is empty, STOP and ask the user what to build.

## Goal

Execute the complete **short flow** automatically, chaining each Spec Kit phase as soon as the previous one finishes:

1. `__SPECKIT_COMMAND_SPECIFY__` (feature description)
2. `__SPECKIT_COMMAND_PLAN__`
3. `__SPECKIT_COMMAND_TASKS__`
4. **Implementation gate** (unless `--bypass`)
5. `__SPECKIT_COMMAND_IMPLEMENT__`
6. `__SPECKIT_COMMAND_CONVERGE__` (once, or looped with `--loop`)

## Execution Steps

Run each phase by **fully following the instructions of the corresponding Spec Kit command** available to you in this project (same commands the user would invoke manually). Do NOT reimplement or shortcut a phase: load that command's instructions and execute them completely, then move on.

### Phase rules (apply to every phase)

- Before creating a run, inspect `.specify/orchestration/flows/` for a
  non-terminal short-flow state matching this feature. If one exists, ask
  whether to resume it; when accepted, restore its flags, current phase,
  completed phases, child `run_id`, pending question, and status instead of
  starting again.
- When no run is resumed, generate a unique `flow_run_id` and atomically create
  `.specify/orchestration/flows/<flow_run_id>/state.json`. Record the same
  fields and update them before and after every phase so an interrupted flow
  can continue without replaying completed phases.
- Ensure `.specify/orchestration/.gitignore` excludes runtime state, never stage
  a flow/run directory, and restrict state-file permissions to the current user
  when supported.
- Announce each phase before starting: `▶ Flow [N/6]: <command>`.
- **User questions are NEVER suppressed — in ANY phase, under ANY flag**: if a phase needs a user decision, clarification, or confirmation (per its own instructions), ASK and WAIT for the answer before continuing. Never auto-answer, never assume defaults for something the phase would normally ask about, never skip a question because the flow is "automatic" or because `--bypass` was passed. `--bypass` removes ONLY the implementation gate, nothing else. Automation chains phases; it does not silence questions.
- When a delegated phase returns `awaiting_user_input`, store its child
  `run_id`, set the flow state to `awaiting_user_input`, and do not advance the
  phase. Ask through the principal CLI, resume that exact child session or
  checkpoint, and mark the phase complete only after the resumed command
  completes. This pause is not a phase failure.
- Questions originating in the flow itself, including the implementation gate,
  are stored in the flow state before asking. Save the answer and clear the
  pending question before continuing.
- If a phase FAILS or its output is invalid, atomically set the flow state to
  `failed`, preserve the current phase and child state, STOP the flow, report
  which phase failed and why, and tell the user how to resume.
- Do not skip phases. Do not reorder phases.

### 1. Specify

Execute `__SPECKIT_COMMAND_SPECIFY__` with the feature description from the user input.

### 2. Plan

Execute `__SPECKIT_COMMAND_PLAN__`. If the user provided tech-stack guidance in the input, pass it along; otherwise derive sensible choices from the spec and existing codebase, and ask the user if the choice is genuinely ambiguous.

### 3. Tasks

Execute `__SPECKIT_COMMAND_TASKS__`. Every task must carry its complete
`[E:category=...|cli=...|model=...|effort=...|context=...]`
assignment.

### 4. Implementation gate

- If `--bypass` was passed: skip this gate entirely and continue.
- Otherwise **STOP and ask the user for confirmation** before implementing. Show a compact summary:
  - Feature directory and branch
  - Task count by phase and assigned executor
  - Anything flagged during planning
  - The question: "Proceed with implementation? (yes / no / adjust)"
- Only continue after an explicit yes. If the user says no or asks for adjustments, stop the flow and apply what they ask.

### 5. Implement

Execute `__SPECKIT_COMMAND_IMPLEMENT__` (the exact executor recorded in each
task label applies).

### 6. Converge

Execute `__SPECKIT_COMMAND_CONVERGE__`:

- **Without `--loop`**: run converge once and report its result (converged or remaining tasks appended).
- **With `--loop`**: if converge appends new tasks, run `__SPECKIT_COMMAND_IMPLEMENT__` again and then converge again. Repeat until converge reports converged, up to a maximum of **5 iterations**. If still not converged after 5, STOP and report what remains.

## Completion report

At the end, output:

- Phases completed (and iterations used if `--loop`)
- Feature directory, spec/plan/tasks paths
- Implementation summary: tasks completed / total
- Converge status: converged or remaining work
- Suggested next step (review, PR, or re-run with `--loop`)

Before reporting success, atomically set the flow state to `completed`, clear
its pending question and child `run_id`, and retain the state as an audit and
resume-safety record.
