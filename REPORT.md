# Computer-Use Automation System — Design Report

## 1. Architecture

The system implements a discover-once, replay-many architecture for automating legacy business applications that do not expose usable APIs.

The implementation uses a simulated Member Servicing System as the target application. The application represents a simplified internal banking interface where an operator can search for a member, open the member record, select an account, and retrieve the current account balance.

The system separates execution into two main paths:

### Discovery

During discovery, an LLM is used to reason about the current application state and determine the next browser action required to accomplish a natural-language goal. Browser interaction is performed through a Playwright-based surface abstraction.

The discovery process follows an observe → decide → act loop. Successful actions are recorded and converted into a structured capability artifact rather than preserving the raw LLM interaction as the production automation.

### Deterministic Replay

After discovery succeeds, the generated artifact becomes the production execution path. Runtime inputs such as `member_id` and `account_type` are substituted into the recorded steps, and the Replay Engine executes those steps without requiring the LLM to make decisions.

The replay engine verifies the expected success checkpoint, extracts the declared output from the resulting page, and returns a structured result.

This separation keeps LLM reasoning out of repeated production execution while retaining it where it is most useful: discovering how to perform a previously unknown workflow.

### Main Components

- **Member Servicing System:** Local FastAPI application representing the legacy business application.
- **Browser Surface:** Playwright abstraction responsible for opening pages, locating controls, clicking, filling fields, reading page state, and capturing screenshots.
- **Discovery Runner:** Executes the LLM-guided workflow against the live application and records the successful path.
- **Capability Artifact:** Versioned JSON representation of the reusable workflow, including typed inputs, outputs, steps, and a success checkpoint.
- **Replay Engine:** Executes saved artifacts deterministically using runtime parameters.
- **Policy Layer:** Restricts allowed domains and actions and prevents unsafe operations.
- **Human Handoff:** Provides a pause/control-transfer/resume path when automation cannot safely continue.
- **Evidence Layer:** Stores structured run information and screenshots for inspection and debugging.

The architecture intentionally keeps the surface interaction layer separate from the capability representation. Playwright is the concrete implementation used for this prototype, but the same replay and artifact concepts can be extended to other computer-use surfaces.

### Key Trade-offs

Playwright was selected because it provides a practical way to demonstrate real UI interaction while keeping the prototype small and understandable. Text and label-based targeting are used instead of application-specific test IDs, making the approach closer to the constraints of legacy enterprise applications.

The prototype favors a small end-to-end implementation over production infrastructure such as distributed workers, queues, persistent orchestration services, or a full operator console. These components would add operational scale but are not required to demonstrate the core discovery-to-replay architecture.

## 2. Artifact schema

A successful discovery run is converted into a JSON capability artifact. The artifact is intentionally separate from the raw LLM transcript so that it can be reviewed, versioned, stored, and invoked repeatedly without requiring the model.

An example capability is `get_account_balance`.

The artifact contains:

- `schema_version` — version of the artifact format.
- `capability_id` — stable identifier for the capability.
- `capability_version` — version of the individual capability.
- `name` and `description` — human-readable description of its purpose.
- `inputs` — typed runtime parameters required by the capability.
- `outputs` — typed values returned to the caller.
- `steps` — ordered deterministic actions discovered during the successful run.
- `success_checkpoint` — condition used to verify that execution reached the intended state.

For the account-balance capability, the runtime contract includes two required string inputs:

- `member_id`
- `account_type`

and returns:

- `balance`

Concrete values used during discovery are parameterized before reuse. For example, the recorded member identifier becomes `{{member_id}}` and the selected account becomes `{{account_type}}`. This allows one discovered flow to be reused for different members and account types rather than recording a new automation for every request.

Each step has an action such as `open`, `fill`, or `click`, together with a target and optional value. Targets are expressed at the capability level rather than embedding Playwright-specific code into the artifact. The Browser Surface is responsible for translating those targets into concrete UI interactions.

For example, the capability can express:

`fill → Member ID → {{member_id}}`

without storing a CSS selector or Playwright call in the artifact. This separation keeps the capability representation independent from the current browser implementation and creates a seam for supporting alternative targeting strategies later.

The artifact also declares the checkpoint `Account Details`. Replay does not assume that the final click succeeded; it verifies that the expected state is actually present before returning success.

The schema is deliberately small for this prototype. A production version could extend targets with multiple locator strategies, application/vendor metadata, tenant overrides, artifact approval state, richer output extraction definitions, and compatibility/version constraints without changing the core discover-once/replay-many model.

## 3. Determinism & error handling

Deterministic replay is the production execution path. Once a capability has been discovered and saved, the Replay Engine executes the recorded steps without asking the LLM what to do next.

At invocation time, runtime values are substituted into artifact parameters. For example:

- `{{member_id}}` becomes `12345`
- `{{account_type}}` becomes `Checking`

The resulting actions are then executed in the same recorded order through the Browser Surface.

### Deterministic targeting

The prototype primarily uses visible labels and text to identify controls. Examples include `Member ID`, `Search Member`, `Open Member`, and the runtime account type.

This was chosen instead of application-specific test IDs because the target environment described in the assignment includes legacy applications where dedicated automation identifiers may not exist.

The artifact itself does not contain Playwright-specific selectors. Target resolution is delegated to the Browser Surface, allowing the targeting implementation to evolve without changing the capability contract.

### Checkpoint verification

Replay does not treat completion of the final action as proof of success.

The capability contains a success checkpoint requiring `Account Details` to be present on the resulting page. If the checkpoint is missing, replay returns a structured `checkpoint_failed` result rather than reporting success.

After checkpoint validation, the current balance is extracted and returned through the capability's output contract.

### Business outcomes

Expected application conditions are distinguished from automation failures.

The prototype demonstrates:

- `MEMBER_NOT_FOUND` — the supplied member identifier does not correspond to a member.
- `ACCOUNT_NOT_FOUND` — the member exists, but the requested account type is unavailable.

These conditions return:

`status = business_outcome`

rather than raising an automation exception. This distinction allows a calling agent to react to a legitimate business result differently from a broken automation.

### Hard failures

Unexpected execution problems return:

`status = failure`

with diagnostic context such as the step number, action, target, reason, and available outputs.

Examples include:

- unsupported actions,
- missing targets,
- checkpoint failures,
- policy violations,
- browser or execution exceptions.

This makes failures inspectable instead of allowing replay to continue blindly after an unexpected condition.

### Recoverable conditions

The current prototype keeps automatic recovery deliberately narrow. It relies on Playwright's normal waiting behavior for ordinary page readiness, but it does not implement generalized retries for session expiration, unexpected dialogs, or repeated transient failures.

In a production implementation, recoverable conditions would be represented explicitly with bounded retry policies, known-dialog handlers, timeout recovery, and retry limits. If recovery were exhausted, the run would transition to the human-intervention path rather than retry indefinitely.

### Validation

Automated tests cover the successful replay path, `MEMBER_NOT_FOUND`, `ACCOUNT_NOT_FOUND`, external-domain policy enforcement, and risky-action policy enforcement.

The successful replay was also manually validated against the live application, where the parameterized `Checking` account workflow returned the expected balance through the structured output contract.

## 4. Heterogeneity & multi-tenant

The prototype is implemented against a browser-based application using Playwright, but the capability artifact is intentionally separated from the concrete browser implementation.

### Surface abstraction

The `BrowserSurface` acts as the boundary between a recorded capability and the technology used to operate an application.

The artifact describes logical operations such as:

- open a target,
- fill a labeled field,
- click a control,
- read the current state.

It does not embed Playwright code directly.

For a modern or legacy web application, another surface implementation could use DOM locators, accessibility information, frames, text matching, or screenshot/coordinate-based targeting depending on what the application exposes.

For a native desktop application, the same higher-level artifact model could be executed by a different surface adapter backed by an OS accessibility API or desktop automation framework.

The Replay Engine would continue to interpret the capability steps while the selected surface implementation would determine how each action is physically performed.

A production artifact could also store multiple targeting strategies for a control, for example a preferred accessibility target followed by text or visual fallbacks. This would allow replay to degrade gracefully when one representation is unavailable.

### Multi-tenant reuse

The capability should conceptually belong to a vendor application and workflow rather than directly to one institution.

For example, a base capability could represent:

`vendor/member-servicing/get-account-balance`

while tenant configuration supplies application-specific details such as:

- entry URL,
- branding-specific labels,
- supported application version,
- locator overrides,
- known dialogs or interstitials.

The ordered business workflow and parameter contract could therefore remain shared while small differences are expressed as tenant- or version-specific overrides.

This avoids creating a completely independent artifact for every institution running the same underlying vendor product.

### Drift detection

Each successful replay provides a signal about compatibility between an artifact and a particular application instance.

Repeated failures at a known target or checkpoint could indicate tenant configuration differences or application-version drift.

A production system could track replay success by vendor, application version, tenant, and capability. An artifact that begins failing consistently could be marked incompatible or routed for rediscovery/review rather than silently changing the production flow.

Per-tenant overrides should remain explicit and reviewable so that a local customization does not unintentionally modify the shared base capability.

This prototype does not implement tenant registries, desktop adapters, or automatic drift management. The important design choice is that these concerns remain outside the core capability contract and can be added through surface adapters and configuration layers rather than requiring the discovery/replay model to be redesigned.

## 5. Escalation & handoff

The system includes a human-in-the-loop path for situations where automation should not continue autonomously.

Escalation can occur when the system encounters a blocked or unsafe condition, particularly when a requested action is classified as risky and requires human intervention.

### Intervention request

When escalation is required, the system creates a structured handoff record containing context about the interrupted run.

The handoff evidence captures information needed to understand why automation stopped and provides a record of the intervention.

A screenshot of the current application state is also captured so that the operator has visual context when taking control.

### Control transfer

The handoff mechanism is designed around the same active browser session used by the automation.

Rather than starting a new browser session and losing application state, automation pauses and leaves the current session available for manual interaction.

At this point control conceptually changes from:

`AUTOMATION → HUMAN`

The human can inspect the current state and perform the required manual action in that live session.

Once the intervention is complete, control can be returned:

`HUMAN → AUTOMATION`

This preserves the browser context accumulated before escalation and provides a clean seam for resuming or completing the workflow.

### Evidence across the handoff

The prototype records handoff evidence separately from normal replay output. Evidence includes the handoff record and a screenshot of the state where intervention occurred.

This makes the escalation inspectable and provides an audit trail showing why autonomous execution stopped.

### Production extension

The prototype intentionally does not implement a full real-time operator console.

In production, the same mechanism could be connected to an operator queue where intervention requests include capability ID, run ID, current step, reason for escalation, screenshot or state snapshot, and control ownership.

The execution service would maintain an explicit control state such as `AUTOMATION`, `WAITING_FOR_HUMAN`, or `HUMAN`. Resume would only be permitted after the operator explicitly releases control.

Operator identity and manual actions would also be appended to the run's audit record.

This keeps the prototype small while preserving the important architectural property: automation can stop rather than taking an unsafe action, preserve the active session, expose that session for intervention, and provide a path for control to return to automation.

## 6. Safety

Safety controls are enforced independently from the LLM's reasoning. A model deciding that an action is useful does not automatically mean the system is permitted to execute it.

### Allowlist enforcement

The policy layer restricts where the automation can operate and which action types it may perform.

The prototype validates targets against an approved application boundary and prevents navigation to unapproved external domains. This prevents a discovered or replayed workflow from leaving the intended application environment.

Actions are also checked against the permitted action set before execution.

Automated tests verify that attempts to navigate to an external domain are blocked.

### Risky and irreversible actions

The system distinguishes ordinary reversible UI interactions from actions that could create meaningful side effects.

Safe operations such as navigation, reading state, filling fields, and approved workflow interactions can proceed automatically when they remain within policy.

Risky actions are handled conservatively rather than being executed automatically. When the policy layer identifies an operation that requires human judgment, autonomous execution is blocked and the human-handoff path can be used.

The test suite includes a case verifying that a risky action is rejected by policy.

This approach intentionally favors stopping and escalating over allowing an LLM or replay sequence to perform an irreversible operation without review.

### Sensitive data and secrets

Capability artifacts are designed to contain parameter placeholders rather than concrete customer values.

For example, the reusable artifact stores:

`{{member_id}}`

instead of permanently embedding the member identifier used during discovery.

Likewise, model API credentials are supplied through environment configuration rather than intentionally stored as capability data.

Artifacts should contain workflow structure and parameter definitions, not credentials, authentication tokens, or raw customer records.

In a production environment, structured logging would additionally apply field-level redaction before persistence, and evidence retention would follow institution-specific security and retention policies.

### Limits

The prototype demonstrates the policy boundary and conservative handling of risky actions, but it is not a complete banking authorization system.

A production implementation would require stronger identity and access controls, encrypted evidence storage, operator authentication, tenant-specific policy configuration, audit retention controls, secret management, and more granular authorization for individual business operations.

The important boundary is that policy enforcement is outside the model's control: neither discovery reasoning nor a recorded artifact is allowed to bypass the configured safety policy.

## 7. Cuts

The implementation intentionally focuses on a complete end-to-end vertical slice rather than production-scale infrastructure.

The following areas were deliberately kept minimal or left out.

### Full operator console

The prototype demonstrates the human-handoff mechanism and preservation of the active automation session, but it does not include a production operator dashboard, authentication system, or intervention queue.

With more time, I would add an operator interface showing pending interventions, current screenshots, run context, control ownership, and explicit take-control/resume actions.

### Generalized recovery

Replay handles known business outcomes and reports unexpected failures explicitly, but generalized recovery for conditions such as session expiration, transient application errors, unexpected dialogs, and slow page loads is intentionally limited.

The next step would be to introduce bounded retry policies and known recovery handlers. Recovery would remain deterministic, with exhausted recovery attempts escalating to a human rather than entering an open-ended retry loop.

### Additional surfaces

Only the browser surface is implemented.

The surface abstraction is intended to support additional adapters for legacy browser applications and native desktop software using accessibility APIs, visual targeting, or OS-level automation.

### Multi-tenant infrastructure

The prototype does not implement tenant registries, vendor-version catalogs, tenant-specific artifact overrides, or automatic drift detection.

A production system would maintain shared base capabilities by vendor/application version and apply explicit tenant-specific configuration or locator overrides where required.

Replay telemetry could then be used to detect compatibility problems and trigger review or rediscovery.

### Advanced data protection

The prototype avoids intentionally placing secrets in artifacts and parameterizes runtime member data, but production financial applications would require stronger controls around evidence storage, log redaction, encryption, retention, access control, and auditability.

### Optional capability platform features

The optional stretch goals such as a capability catalog/API, artifact approval lifecycle, confidence scoring, bounded LLM replay recovery, and multi-run stability measurement were not prioritized.

The focus was instead placed on the required vertical slice:

`natural-language goal → LLM discovery → structured capability artifact → deterministic replay → structured outcomes → policy enforcement → human escalation → evidence`

If continuing the project, I would prioritize stronger recovery handling and richer target definitions first, followed by an operator interface and cross-tenant artifact specialization.

