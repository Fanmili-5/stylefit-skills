# Luna complex diagnostic v2

Status: construction and offline oracle validation. No v2 performance claim exists yet.

## Model and budget

Owner authorized 60 additional tasks on 2026-10-22. Preserve the 180-task ledger; the new lifetime cap is 240. All generation, model grading, failures and retries in this round count toward the 60. Explicit model: `gpt-6-luna`; reasoning effort: `medium`. No inherited model choice, no other-model fallback. Keep requested model and available response metadata distinct; a model name emitted in answer text is not identity evidence.

Planned allocation: one preflight, 36 initial outputs (6 development and 6 held-out tasks x 3 arms), 12 code feedback/revision tasks (all four code cases x 3 arms), 8 blinded text-case grading tasks, 2 blinded code-style grading tasks (one batch of the two code cases per phase), and at most 1 failure/format retry. Planned base use 59, hard maximum 60. This allocation was finalized after preflight and before any task generation, to cover code style rather than reuse arbitrary variable-length success thresholds. Each CLI task is one accounting unit; underlying provider retries are not an exactly observable API-request count. Artifact generation is text-only, with deterministic local code execution between the two code turns. There is no unrestricted model-driven tool loop hidden inside a unit.

## Fair comparisons

Arms: a normal task prompt, the same prompt plus an explicit complete checklist, and the same prompt plus OwnVoice. Identical task materials, user constraints, style samples, output schema and resource allowance. The checklist represents a strong ordinary-prompt baseline; it must preserve the relevant skill information without naming OwnVoice. Report instruction/prompt lengths and actual usage when available. A skill benefit over bare prompts alone supports reusable workflow value, not new model capability.

All cases are synthetic. Style samples demonstrate conventions with unrelated facts; target tasks do not enumerate the traits to be imitated. No project-owner profile is loaded. Reference facts and obligations are typed/attributed where ambiguity would invalidate grading. Do not hide unprovided domain facts in the oracle.

## Tasks and checks

Code cases span multiple files, public compatibility, keyword arguments, exceptional and missing-value behavior, stable ordering and input mutation. Each arm gets one initial output, an equal local-feedback opportunity and one revision. Local hidden tests score final behavior separately from the visible feedback. All original implementations must pass; seeded faulty variants must fail before model generation.

Research cases combine sources with corrections, conflicting versions, units, scope limits and unknown values. Email cases combine quoted history, current brief, contextual metadata and recipient-specific actions. Exact facts and structured ledgers are checked locally. Raw text can contradict a correct ledger, so local checks are not semantic proof.

Luna text grading sees randomly relabelled outputs and common raw materials, not method labels or intended rankings. It checks fidelity, unsupported obligations, sample-fact leakage and style alignment. It is same-family model review, not independent human preference evidence. It cannot overrule a failed executable contract or turn an unknown source fact into a fact.

## Development and holdout

Freeze tasks, oracles, checklist, runner, model settings and the initial candidate before development. Review six development cases, then allow at most one change grounded in an actual failure. Preserve the original candidate. Freeze the final candidate before held-out generation; do not inspect those outputs mid-batch or tune on them. Report every cell, first/final code outputs, repairs, invalid outputs and negative results. Small task counts do not support population or significance claims.

No publication without approval of a concrete candidate. Raw traces, grading mappings and private review data stay under `.local/`.
