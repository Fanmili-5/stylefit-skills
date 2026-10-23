# v0.1 pilot protocol

This is a one-participant preference pilot, not a population study or authorship detector benchmark.
Chinese and English each cover code, research and email, with generation and rewrite modes.
The private participant profile is based on six explicit preference choices, not historical writing samples.

## Allocation and stopping
Cap: 180 started CLI generation tasks, including failures and retries. This is not a promise of a particular API bill or an exact count of hidden provider-side requests.
Preflight 2; pilot 6 tasks x 3 conditions x Codex = 18; formal 24 x 3 x 2 runtimes = 144; mismatched profile 6 x 2 = 12. Total planned 176, at most 4 retries.
Use current configured Codex and Claude; record response-reported models when available. Two CLIs do not automatically mean two distinct model families. If a runtime fails preflight, do not launch its full matrix or silently purchase a substitute.
No automatic retries or ledger resets. Successful jobs are never regenerated to obtain a nicer answer. An interrupted started job consumes a task.

## Conditions and controls
Plain prompt, pinned upstream skill (John's code-humanizer for code; blader/humanizer for prose), and OwnVoice receive identical source packets, constraints and domain/language preferences.
Conditions are explicitly loaded into a text-only prompt. Disable installed skill discovery, plugins and tools as supported by each CLI; log tool-use contamination if observed. This tests skill-instruction effect, not automatic invocation/routing quality.
Fixtures are authored synthetic material and are labelled. Source IDs such as [S1] identify local synthetic packets, not invented real papers.
Before formal generation, freeze profile, task/test definitions, instructions, baselines, checker and runner hashes. Do not edit these in place during formal evaluation. A failure of a checker discovered afterwards requires a disclosed new evaluation version, not silent rescoring.

## Checks and blind review
Code checks are restricted Python fixture checks: required signatures, selected normal/boundary/keyword cases, return types, exceptions and mutation. They are not a general execution sandbox or equivalence proof.
Text checks preserve exact spans and selected markers. Semantic fidelity remains a human-review task; passing a string check is not proof of truth or preserved claim strength.
Prepare 12 baseline pairs, one for each domain/language/runtime cell, alternating plain/upstream for 6 comparisons per baseline. Select sample indices deterministically before reading outputs. Add 6 matched/mismatched profile pairs, one per domain/language cell with balanced runtimes.
Hide condition/runtime names, use deterministic randomized left/right placement, permit ties, and ask separately about style fit, clarity and willingness to use. Mapping and feedback stay private.
Pilot gate: at least 4 of 6 wins against each baseline and 4 of 6 against mismatched profiles. Report counts and ties, not a significance claim. Report by domain and runtime even when results are negative.
If only one runtime passes preflight, freeze and report a single-runtime pilot: use 6 baseline pairs (3 per baseline; gate 2 wins of 3) and 6 mismatch pairs (gate 4 of 6). Do not claim cross-model evidence or reallocate the absent runtime's tasks to favorable rerolls.
Known critical constraint regressions block stable release. If constraints pass but preference benefit is insufficient, label only a technical preview. Do not tune against these formal outputs and rerun them as unseen evaluation.

## Publication
Raw runs, profile and blind mappings are private by default. Publish only synthetic fixtures, permitted baseline material with licenses, evaluation code, aggregate results and explicitly approved examples. Do not publish source packets from coursework, private mail, credentials, provider URLs or machine logs.
