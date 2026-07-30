---
description: Interactively build the global models.json, validate reusable CLI execution recipes, configure implementation allocation, and assign ordered model executors to each eligible Spec Kit command.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user
may provide CLI names, executable paths, model-picker output, unlisted model
IDs, official documentation, administration instructions, or corrections to a
proposed execution recipe.

## Goal

Build or update the global registry at `~/.specify/models.json`.

This command is a universal registry builder. It must learn enough about the
CLIs selected by the user to construct the file; it must not contain or rely on
a built-in catalog of CLI names, model names, model aliases, or vendor-specific
commands. A CLI or model used in examples elsewhere is never evidence that it
exists on this machine.

The completed registry has four operational sections:

- `models`: an array whose entries are keyed by canonical model name. Each
  model records the CLIs that can run it, the exact model name used by each CLI,
  the effective context window, supported effort levels, and a complete
  OpenRouter-derived description.
- `clis`: an array whose entries are keyed by CLI name. Each CLI records a
  structured recipe that explains how to launch it with the selected model,
  input text, effort level, context window, project working directory, and how
  to capture or reconstruct a resumable session.
- `commands`: an array whose entries are keyed by eligible Spec Kit command
  name. Each command records an ordered list of user-approved CLI, model,
  effort, and context-window combinations. The first combination is the
  default and the remaining combinations are alternatives.
- `implementation`: a user-approved policy for implementation tasks. It groups
  exact CLI/model/effort/context profiles into the fixed capability categories
  `max`, `high`, `medium`, and `low`, then records what percentage of the tasks
  in each category the user wants assigned to each CLI.

This command does **not** choose a manager, assign individual implementation
tasks, or execute workflow commands. It constructs the policy that `tasks`
later uses and analyzes each eligible command's actual workflow requirements to
recommend its executors.

## Non-Negotiable Rules

1. Always write the global file `~/.specify/models.json`. Do not create a
   project-local `.specify/models.json`.
2. Ask the user which CLIs to integrate. Detecting an executable does not grant
   permission to add it automatically.
3. Do not hard-code knowledge for a particular CLI or model. Learn from the
   executable, official documentation, and the user.
4. Ask whether the user wants to add models that the selected CLI does not
   display but can execute. Treat those models exactly like displayed models.
5. The final JSON contains no discovery source, verification status, hidden
   flag, or distinction between automatically discovered and user-provided
   information.
6. Never persist an incomplete model or a CLI recipe that cannot execute and
   resume delegated work. Keep incomplete work only in the current conversation
   and ask for the missing information.
7. Never store credentials, API keys, authorization headers, session tokens,
   or secret environment values.
8. Represent process arguments as an array. Never store a shell command string
   that requires interpolation or evaluation.
9. Assign executors only to `constitution`, `specify`, `clarify`, `plan`,
   `checklist`, `tasks`, `analyze`, `taskstoissues`, and `converge`. Never add a
   command assignment for `models`, `implement`, `flow-quick`, or `flow-full`.
10. Recommendations are advisory. The user decides the default executor and
    every ordered alternative.
11. Never embed a vendor, CLI, model, category assignment, percentage, or
    priority as a built-in default. Ask the user and store only the policy they
    approve for their own environment.

## Execution Steps

### 1. Load the existing global registry

Resolve `~/.specify/models.json` using the host user's home directory.

- If it does not exist, start with empty `models`, `clis`, and `commands`
  arrays plus an unconfigured `implementation` section.
- If it exists, parse and validate it before doing anything else.
- If it is a valid version 2 registry, treat it as a migration candidate:
  preserve its models, CLIs, and command assignments; learn and validate the
  new session contract for every CLI; collect the user's implementation
  categories and allocation policy; show the complete proposed migration; and
  write version 3 only after user confirmation. Never partially upgrade it.
- If the file is invalid JSON or does not follow the schema in this command,
  and is not a valid version 2 migration candidate, STOP and show the
  validation errors. Do not overwrite it.
- Preserve integrations the user does not select during this run.
- Never display secrets found in surrounding CLI configuration.

The command is incremental: it can create the registry, add another CLI,
refresh an existing CLI, add models, update model metadata, or revise command
assignments without rebuilding unrelated integrations.

### 2. Detect candidates and ask which CLIs to integrate

Inspect the local environment for executable AI CLIs using available runtime
evidence such as PATH, installed Spec Kit integration metadata, running host
context, package-manager metadata, and explicit user input.

Present the detected candidates with their executable path and version when
available. Then **ask the user which detected CLIs to integrate**. The prompt
must support:

- selecting one or more detected CLIs;
- entering an executable name or absolute path that was not detected;
- refreshing a CLI already present in the global registry;
- declining all candidates without changing the file.

Do not assume the CLI hosting this conversation is the only CLI to integrate.
Do not automatically integrate every detected executable.

### 3. Learn how each selected CLI is administered

For every selected CLI, determine:

- executable name or absolute path;
- installed version;
- non-interactive invocation mode;
- how to list or select models;
- how to pass the exact model ID;
- how to provide the task text: standard input, argument, or file;
- how to set reasoning/effort and which values are accepted;
- how to set or enforce the context window;
- how to set the project working directory;
- whether the CLI exposes durable sessions and how to capture their exact ID;
- how to resume a session with additional user input without replaying work;
- how completion and a non-zero failure are reported.

Use this evidence in order:

1. Safe local introspection such as version, help, config inspection, and
   native model-list commands.
2. Official documentation for the installed CLI version.
3. User-provided documentation or administration instructions.

If local introspection and official sites do not explain how the CLI is
administered, ask whether the user can provide a reference or explain the
required commands. Do not improvise vendor-specific flags.

An interactive slash command is not automatically a shell command. If the
model picker can only be opened interactively, ask the user to open it and
provide its complete contents.

### 4. Discover all models the user wants registered

Obtain the displayed model list from the strongest mechanism available:

1. native machine-readable model-list command or API;
2. native interactive model picker supplied by the user;
3. official documentation that applies to the installed CLI and account;
4. an explicit model list supplied by the user.

Preserve the exact model identifier accepted by the CLI.

After collecting the displayed list, always ask:

> Do you want to add any model that this CLI does not display but you know it
> can execute?

For every additional model, collect its exact CLI model ID and process it
through the same context, effort, OpenRouter enrichment, and execution checks
as any displayed model. The final registry must not label it as hidden,
unlisted, manual, user-provided, or less trusted.

Resolve a canonical model key for each model. Prefer the exact OpenRouter model
ID when a match exists. Otherwise ask the user for the stable
`provider/model-name` key to use. Never derive an unfamiliar canonical key from
the model name alone.

If the same canonical model is available through multiple CLIs, create one
entry in `models` and append one availability entry per CLI. For each
availability collect:

- `cli`: key of the corresponding entry in `clis`;
- `model`: exact identifier passed to that CLI;
- `context_window`: effective maximum context accepted through that CLI;
- `effort_levels`: exact effort values that combination accepts, or an empty
  array when effort is unsupported.

The effective CLI context window wins over a larger theoretical provider
window. A context window must be a positive integer token count; labels such as
`large` or `1M` must be converted to exact tokens before writing.

### 5. Build the complete model description

Use current OpenRouter data to populate every model's `description`. Fetch
current JSON data rather than relying on memory or a static model table:

| Data | Preferred OpenRouter endpoint | Required output |
|---|---|---|
| Model identity, pricing, context | `https://openrouter.ai/api/v1/models` | canonical ID and input/output price |
| Intelligence | `https://openrouter.ai/api/frontend/v1/rankings/benchmarks` | normalized score and concise summary |
| Speed | `https://openrouter.ai/api/frontend/v1/rankings/performance` | normalized score, throughput, and concise summary |

Match against the live returned IDs and metadata. Do not maintain a static alias
table in this command.

Every `description` must contain:

- `intelligence.score`: normalized number from 0 through 100;
- `intelligence.summary`: concise capability description;
- `speed.score`: normalized number from 0 through 100;
- `speed.tokens_per_second`: positive measured or documented throughput;
- `speed.summary`: concise speed/latency description;
- `cost.input_per_million`: USD cost per one million input tokens;
- `cost.output_per_million`: USD cost per one million output tokens;
- `cost.currency`: `USD`;
- `benefits`: a non-empty array describing the model's strongest practical
  uses based on its intelligence, speed, context, capabilities, and cost.

Zero is valid for a free model's input or output cost. Missing data is not the
same as zero.

When OpenRouter does not contain a selected model or lacks any required value:

1. Look for official provider documentation.
2. Ask whether the user can provide a reference containing the missing
   intelligence, speed, cost, context, or capability information.
3. Use the supplied reference to complete the same `description` shape.
4. If the data still cannot be completed, do not add or update that model and
   do not finalize a new registry that depends on it.

Do not persist source, provenance, confidence, verification, or discovery
metadata in the final JSON.

### 6. Construct a reusable CLI execution recipe

Build one CLI entry from the learned administration contract. The recipe must
be data, not prose and not a vendor-specific block injected by the integration
that installed this command.

Required recipe behavior:

- `executable` identifies the program to launch.
- `version` records the installed version for which the recipe was built.
- `execution.argv` is the argument array passed after the executable.
- `{model}` marks the exact CLI model ID.
- `{text}` marks task text when text is passed as an argument or file path.
- `{effort}` marks the effort value when configurable.
- `{context_window}` marks the token limit when configurable.
- `{project_root}` marks the working directory.
- `{run_id}` and `{run_dir}` identify the durable orchestration state.
- `{session_id}` is permitted only in a native resume argument array.
- `execution.text` defines whether text travels by `stdin`, `argument`, or
  `file`.
- `execution.effort` defines whether effort is set by `argument`, `config`,
  `fixed`, or `unsupported`.
- `execution.context_window` defines whether context is set by `argument`,
  `config`, `fixed`, or `automatic`.
- `execution.session` defines one of two exact modes:
  - `native`: the CLI persists a session. Record how its ID is captured and a
    structured resume recipe whose argv contains `{session_id}`. The resume
    argv may also repeat `{model}`, `{effort}`, `{context_window}`,
    `{project_root}`, `{run_id}`, or `{run_dir}` when the CLI requires them.
  - `checkpoint`: the CLI has no usable native resume mechanism. Session
    capture is `none`, `resume` is `null`, and the principal relaunches the same
    execution recipe with the durable checkpoint and answer.

If effort or context is not exposed as a command argument, record its real
mode. Do not invent a flag merely to include a placeholder.

Do not mark a CLI as `native` merely because it stores conversation history.
The session ID must be observable and the resume invocation must accept
additional text non-interactively. If either part cannot be established, use
`checkpoint`.

### 7. Test before writing

Validate the learned contract in increasing order of cost:

1. Confirm the executable resolves and its version matches the recipe.
2. Confirm the argument structure is accepted using non-consuming help,
   validation, or dry-run support when available.
3. Confirm text transport and working-directory behavior.
4. Confirm model selection, effort values, and context behavior.
5. Detect silent fallback to a default model when the CLI exposes enough
   runtime information to do so.
6. For native sessions, confirm that a session ID can be captured and that a
   second invocation resumes it without repeating the first action.
7. For checkpoint sessions, confirm that the initial execution recipe accepts
   a continuation prompt containing saved state and user answers.

Before a probe that may consume paid tokens, quota, or create remote state,
explain the probe and ask the user for approval. If no safe probe exists, ask
the user to run or confirm the invocation. Do not write a recipe known to fail.

These checks are construction steps only. Do not write `verified`, `status`,
`source`, `listed`, or similar fields to the registry.

### 8. Configure implementation categories and task allocation

Build the `implementation` section interactively after the model and CLI
catalogs are complete. This section is personal configuration: derive no
assignments from examples, the current host CLI, vendor market share, or a
hard-coded cost formula.

#### 8.1 Confirm implementation profiles

Explain that a profile is an exact combination of:

- one existing canonical `model`;
- one `cli` present in that model's availability;
- one supported `effort`, or `null` when effort is unsupported;
- one positive `context_window` no larger than the effective availability
  limit.

Ask which profiles the user wants available for implementation and ask the user
to place each selected profile in one of exactly four capability categories:

- `max`: the user's highest-capability profiles, normally reserved for work
  where losing reasoning quality or context would be unacceptable;
- `high`: strong profiles for substantial implementation work;
- `medium`: balanced profiles for regular implementation work;
- `low`: economical profiles for bounded, mechanical work.

Use intelligence, benefits, context, speed, and OpenRouter cost only to explain
and recommend placements. Also ask about the user's real subscription, quota,
and relative-cost constraints because public per-token prices may not represent
their actual cost. The user makes every final placement.

The same canonical model and CLI may appear in more than one category when the
user deliberately chooses different effort or context values. Do not collapse
those profiles. Within each category, ask the user to order profiles from first
choice to last choice. An empty category is allowed, but explain that `tasks`
will stop if a task requires a category with no usable profile.

Do not require every catalog model to participate in implementation. Ask the
user explicitly whether an unassigned model is intentionally command-only
before accepting the configuration.

#### 8.2 Collect the user's per-category allocation policy

The allocation measurement is `task_count`. Ask the user separately for each
non-empty category:

1. What percentage of that category's tasks each participating CLI should
   receive.
2. The target order to use when integer rounding produces equal remainders.

Only CLIs with at least one profile in the category may receive a percentage.
Percentages may include zero for a fallback-only CLI and must sum exactly to 100
inside each non-empty category. An empty category has an empty target array.

Explain that `tasks` first classifies the complete task set, counts tasks in
each category, and then converts these percentages into whole-task quotas using
the largest-remainder method. A percentage is not attached to a particular
model: it allocates tasks to a CLI within one category. The first valid profile
for that CLI in the category's user-approved profile order supplies the exact
model, effort, and context.

Category, effective context, and profile validity are hard constraints.
Allocation never authorizes moving a task to another category. If task-specific
constraints make an exact quota impossible, `tasks` keeps the category,
chooses another valid profile in that category, and reports the deviation.

Show the complete proposed categories, ordered profiles, and per-category
targets. Ask the user to confirm them before storing the policy. `tasks` must be
able to consume this policy without asking the user to recreate it.

### 9. Recommend and confirm command executors

After the model and CLI catalogs are complete, build assignments for exactly
these eligible commands:

1. `constitution`
2. `specify`
3. `clarify`
4. `plan`
5. `checklist`
6. `tasks`
7. `analyze`
8. `taskstoissues`
9. `converge`

Do not create assignments for:

- `models`, because it constructs this registry;
- `implement`, because it executes the CLI/model assignments already attached
  to individual implementation tasks;
- `flow-quick` and `flow-full`, because they only run command sequences.

For each eligible command:

1. Read the command's purpose, workflow, expected artifacts, and operational
   constraints. Evaluate those requirements directly.
2. Evaluate available CLI/model combinations using:
   - model intelligence and relevant benefits;
   - effective context window through that CLI;
   - supported effort levels;
   - speed;
   - input and output cost;
   - the tested CLI execution recipe.
3. Recommend one default combination and explain briefly why it fits.
4. Offer other viable combinations, including a different CLI or model when
   available so one unavailable route does not block the command.
5. Ask the user to accept the recommendation, choose another combination, and
   optionally add one or more alternatives.

Allow the user to accept all recommendations together, then review or override
individual commands. Never save a recommendation as a decision before the user
confirms it.

Each assignment is an ordered array:

- index `0` is the default executor;
- index `1` and later are alternatives tried in order when the preceding
  combination cannot be launched or its CLI/model is unavailable;
- the array order is not load balancing and does not authorize parallel
  execution.

Each combination contains:

- `cli`: an existing key from `clis`;
- `model`: an existing canonical key from `models`;
- `effort`: one exact effort value supported by that model through that CLI, or
  `null` only when the CLI does not support configurable effort;
- `context_window`: a positive token count no larger than that model's
  effective context window through the selected CLI.

The assignment uses the canonical model key, not the CLI-specific model string.
At execution time, the selected model's matching availability entry supplies
the exact CLI model ID.

### 10. Show the proposed registry change

Before writing:

1. Show the CLIs that will be added or refreshed.
2. Show every model and its CLI-specific context and effort values.
3. Show intelligence, speed, cost, and benefits.
4. Show the structured execution recipe with secrets redacted.
5. Show whether each CLI uses native session resume or checkpoint continuation,
   including the native capture and resume recipe when applicable.
6. Show all four implementation categories and every ordered execution profile.
7. Show the task-count percentages and tie-break order for every category.
8. Show the default and ordered alternatives for every eligible command,
   including CLI, model, effort, and context window.
9. Explain which existing entries or assignments will change or be removed.
10. Ask the user to confirm the final update.

Do not remove a CLI, model, or availability merely because discovery failed in
this run. Removal requires explicit user confirmation.

### 11. Write the global JSON

Write this schema to `~/.specify/models.json`:

```json
{
  "version": 3,
  "models": [
    {
      "<canonical-model-id>": {
        "availability": [
          {
            "cli": "<cli-key>",
            "model": "<exact-cli-model-id>",
            "context_window": 0,
            "effort_levels": ["<exact-effort-value>"]
          }
        ],
        "description": {
          "intelligence": {
            "score": 0,
            "summary": "<capability summary>"
          },
          "speed": {
            "score": 0,
            "tokens_per_second": 0,
            "summary": "<speed summary>"
          },
          "cost": {
            "input_per_million": 0,
            "output_per_million": 0,
            "currency": "USD"
          },
          "benefits": [
            "<strong practical use>"
          ]
        }
      }
    }
  ],
  "clis": [
    {
      "<cli-key>": {
        "executable": "<executable-name-or-absolute-path>",
        "version": "<installed-version>",
        "execution": {
          "argv": ["<argument>", "{model}"],
          "text": {
            "transport": "stdin | argument | file",
            "placeholder": "{text}",
            "argument": "<flag-or-null>"
          },
          "effort": {
            "mode": "argument | config | fixed | unsupported",
            "placeholder": "{effort}",
            "argument": "<flag-or-null>"
          },
          "context_window": {
            "mode": "argument | config | fixed | automatic",
            "placeholder": "{context_window}",
            "argument": "<flag-or-null>"
          },
          "session": {
            "mode": "native | checkpoint",
            "capture": {
              "method": "json_pointer | output_regex | none",
              "selector": "<pointer-pattern-or-null>"
            },
            "resume": {
              "argv": ["<argument>", "{session_id}"],
              "text": {
                "transport": "stdin | argument | file",
                "placeholder": "{text}",
                "argument": "<flag-or-null>"
              }
            }
          },
          "working_directory": "{project_root}"
        }
      }
    }
  ],
  "commands": [
    {
      "<eligible-command-name>": [
        {
          "cli": "<cli-key>",
          "model": "<canonical-model-id>",
          "effort": "<exact-effort-value-or-null>",
          "context_window": 0
        }
      ]
    }
  ],
  "implementation": {
    "allocation_measurement": "task_count",
    "categories": [
      {
        "max": {
          "profiles": [
            {
              "cli": "<cli-key>",
              "model": "<canonical-model-id>",
              "effort": "<exact-effort-value-or-null>",
              "context_window": 0
            }
          ],
          "targets": [
            {
              "<cli-key>": 0
            }
          ]
        }
      },
      {
        "high": {
          "profiles": [],
          "targets": []
        }
      },
      {
        "medium": {
          "profiles": [],
          "targets": []
        }
      },
      {
        "low": {
          "profiles": [],
          "targets": []
        }
      }
    ]
  }
}
```

The zeroes and angle-bracket strings above are schema placeholders, not values
to copy. Every written value must be complete and reflect the selected CLI and
model. The `session.resume` object shown is the native-session shape. For
checkpoint mode, write `capture.method: "none"`, `capture.selector: null`, and
`resume: null`.

Validation before committing the file:

- `version` equals `3`.
- `models`, `clis`, and `commands` are non-empty arrays and `implementation`
  is a non-empty object.
- Every element of the three arrays is an object with exactly one dynamic key.
- Canonical model keys, CLI keys, and command keys are unique.
- Every model has at least one availability.
- Every availability references an existing CLI key.
- Every context window is a positive integer.
- Every effort level is an exact value accepted by that CLI/model combination.
- Every model description contains complete intelligence, speed, cost, and
  non-empty benefits.
- Every CLI has a non-empty executable, version, argument array, text
  transport, effort mode, context mode, session mode, and working directory.
- A native session recipe has a non-`none` capture method, a non-empty selector,
  and a resume argv containing `{session_id}` plus a valid text transport.
- A checkpoint session recipe has capture method `none`, selector `null`, and
  `resume: null`.
- The registry stores session recipes but never runtime session IDs, questions,
  answers, or checkpoints.
- `commands` contains exactly the nine eligible command keys and none of the
  four excluded command keys.
- Every eligible command has at least one executor combination.
- The first combination is the default and later combinations are ordered
  alternatives, with no duplicate combination in the same command.
- Every command combination references an existing canonical model and CLI.
- The referenced model has an availability entry for the referenced CLI.
- The selected effort is listed in that availability, or is `null` only when
  effort is unsupported.
- The selected context window is positive and does not exceed the effective
  context window in that availability.
- `implementation.categories` contains exactly one entry for each of `max`,
  `high`, `medium`, and `low`, with no other category.
- `implementation.allocation_measurement` equals `task_count`.
- Every category contains `profiles` and ordered `targets` arrays.
- Every implementation profile references an existing canonical model and CLI,
  the model is available through that CLI, effort is supported, and context is
  positive and no larger than the availability limit.
- No exact implementation profile is duplicated within a category. Reusing a
  model in another category requires a deliberate effort or context profile.
- Every catalog model omitted from implementation was explicitly confirmed as
  command-only by the user.
- In every non-empty category, targets use unique CLI keys present in that
  category's profiles, contain numbers from 0 through 100, include every CLI
  represented by a profile, and sum exactly to 100.
- Every empty category has an empty targets array. Target array order is the
  user-approved tie-break order for equal largest remainders.
- Every placeholder used by `argv` is defined by the recipe.
- `argv` does not contain the executable and is never a shell command string.
- The JSON contains no credentials and no construction-only status or
  provenance fields.
- Reparse the file after writing and run the same validation again.

Write atomically: create a temporary file beside the destination, validate it,
then replace the destination so an interrupted update cannot corrupt the
existing registry.

### 12. Completion report

Report:

- global path written;
- CLIs added or refreshed;
- models added or updated;
- effective context window and effort levels for every CLI/model pairing;
- intelligence, speed, input/output cost, and benefits for every model;
- exact structured execution recipe for every CLI, with secrets redacted;
- native-session or checkpoint resume behavior for every CLI;
- the four implementation categories and their ordered profiles;
- per-category task-count targets and tie-break order;
- default and ordered alternative executors for every eligible command;
- entries preserved unchanged;
- any model omitted because its required information could not be completed.

Remind the user to rerun this command after installing, removing, or upgrading a
CLI, changing account model access, or learning that an additional unlisted
model is available.
