# Computer-Use Automation System

A prototype browser automation system that uses an LLM during workflow discovery, converts successful discovery runs into reusable structured capability artifacts, and executes those artifacts deterministically with Playwright.

The project uses a simulated Member Servicing System to demonstrate account-balance retrieval, structured outcomes, safety controls, evidence capture, and human escalation.

## What This Demonstrates

The implemented vertical slice is:

**Natural-language goal → LLM discovery → structured capability artifact → deterministic replay → structured outcomes → policy enforcement → human escalation → evidence**

The LLM is used during discovery to determine how to accomplish a goal through the browser interface. Once a successful workflow is discovered, it is converted into a parameterized JSON capability artifact.

Replay then executes the saved artifact deterministically without requiring the LLM to rediscover the workflow.

## Core Features

- LLM-guided browser workflow discovery
- Playwright-based browser interaction
- Structured JSON capability artifacts
- Runtime input parameterization
- Deterministic artifact replay
- Output extraction from browser pages
- Explicit business outcomes
- Safety policy enforcement
- Human handoff for risky actions
- Discovery and replay evidence capture
- Automated replay and policy tests

## Example Capability

The primary demonstrated capability retrieves the balance of a selected account for a member.

Example runtime inputs:

```json
{
  "member_id": "12345",
  "account_type": "Checking"
}
```

Successful output:

```json
{
  "status": "success",
  "outputs": {
    "balance": "3120.25"
  }
}
```

The capability artifact is available at:

```text
evidence/discovered_account_balance.json
```

## Project Structure

```text
computer-use-automation/
├── README.md
├── REPORT.md
├── evidence/
│   ├── discovered_account_balance.json
│   ├── discovery_run.json
│   ├── discovery_success.png
│   ├── handoff_step_2.png
│   ├── human_handoff.json
│   ├── replay_error_cases.log
│   └── replay_success.log
└── demo-app/
    ├── app.py
    ├── database.py
    ├── data.py
    ├── requirements.txt
    ├── run_discovery.py
    ├── run_replay.py
    ├── run_handoff_demo.py
    ├── test_replay.py
    ├── automation/
    └── artifacts/
```

## Setup

Move into the application directory:

```bash
cd demo-app
```

Create and activate a virtual environment if desired, then install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Install the Playwright Chromium browser:

```bash
python3 -m playwright install chromium
```

## OpenAI API Key

LLM-assisted discovery requires an OpenAI API key supplied through an environment variable.

Example:

```bash
export OPENAI_API_KEY="your-api-key"
```

Do not commit API keys or other secrets to the repository.

## Start the Demo Application

From `demo-app`:

```bash
python3 -m uvicorn app:app --reload
```

The simulated Member Servicing System runs locally at:

```text
http://127.0.0.1:8000
```

Keep the application running while executing discovery or replay in another terminal.

## Run Discovery

With the application running and `OPENAI_API_KEY` configured:

```bash
python3 run_discovery.py
```

Discovery uses browser interaction and LLM reasoning to determine a successful workflow and produce a structured capability artifact.

## Run Deterministic Replay

```bash
python3 run_replay.py
```

The replay engine substitutes runtime parameters into the saved artifact and executes the recorded browser operations deterministically.

For the demonstrated input:

```text
member_id = 12345
account_type = Checking
```

the expected balance is:

```text
3120.25
```

## Structured Outcomes

The replay engine distinguishes successful execution from expected business outcomes.

Examples include:

```text
MEMBER_NOT_FOUND
ACCOUNT_NOT_FOUND
```

These conditions are returned as structured business outcomes rather than being treated as generic browser failures.

## Safety and Human Handoff

The prototype includes policy checks designed to prevent unsafe execution.

The test suite verifies that:

- navigation to an external domain is blocked;
- risky actions are blocked by policy;
- workflows requiring escalation can generate human-handoff evidence.

Human-handoff evidence is included in the `evidence/` directory.

## Tests

Run:

```bash
python3 -m pytest test_replay.py -v
```

The test suite covers:

1. successful Checking account retrieval;
2. account-not-found handling;
3. member-not-found handling;
4. external-domain policy blocking;
5. risky-action policy blocking.

Current verified result:

```text
5 passed
```

## Evidence

The root `evidence/` directory contains representative evidence from the implemented workflow, including:

- the discovered capability artifact;
- discovery execution data;
- discovery success screenshot;
- successful deterministic replay log;
- exceptional/error replay test log;
- human-handoff record;
- human-handoff screenshot.

## Design Report

See [`REPORT.md`](REPORT.md) for the detailed system design, architecture decisions, discovery and replay approach, safety model, limitations, production considerations, and intentionally deferred stretch goals.

## Scope

This repository focuses on the required end-to-end vertical slice rather than attempting to build a complete production automation platform.

Optional platform capabilities such as a capability catalog/API, artifact approval lifecycle, confidence scoring, advanced replay recovery, and multi-run stability measurement were intentionally not prioritized.

The implementation instead focuses on demonstrating a clear separation between probabilistic discovery and deterministic execution, with structured outcomes, safety controls, human escalation, and auditable evidence.