# Technical preview, 2026-10-22

This preview implements four portable skills: profile calibration, code, research writing and email. It supports Chinese and English and both generation and rewriting. Python is the only code language evaluated in this round. The participant supplied six explicit preference choices, not historical writing samples.

## Formal constraint checks

The frozen synthetic set contains 24 tasks. Each condition receives the same task and domain/language preferences. This measures any added value of the skill instructions beyond simply providing the profile.

| Condition | Completed | Passed the frozen automated checks |
| --- | ---: | ---: |
| Plain prompt with preferences | 24 | 24 |
| Pinned upstream skill with preferences | 24 | 24 |
| OwnVoice with preferences | 24 | 24 |

Across conditions, the code subset has 24 outputs tested against finite normal, boundary, keyword-call, return-type, exception-type and mutation fixtures. The research and email subsets each have 24 outputs checked for protected quantities/spans and selected meaning markers. All passed those checks. This does not establish a style advantage or full semantic preservation.

All six contrasting-preference outputs also completed and passed the same applicable checks. Total ledger use is 99 of the 180-task cap: 72 formal outputs, 6 contrast outputs, 18 development outputs, 1 successful preflight and 2 failed preflight attempts. There are no running generation tasks.

The implementing assistant also inspected the 24 OwnVoice artifacts against their packets. This is an internal review, not an independent or blinded fidelity assessment. It found no additional content/contract problem within that inspection. In the plain condition, a rewritten `clamp_values` error message changed while its exception type stayed the same; the frozen fixture did not flag it. Exception-message coverage is incomplete, and the formal scores have not been silently revised to imply broader equivalence.

## Runtime and development record

Codex CLI 0.163.0 passed its preflight. Claude Code 2.1.303 timed out twice, including one counted retry; a separate connection probe also timed out. The planned single-runtime fallback was used. No absent-runtime budget was reassigned to favorable rerolls.

The successful Codex response events did not report model identifiers. These are CLI-runtime observations, not verified model-family comparisons. Instructions were explicitly loaded into tool-disabled prompts; this does not test automatic host skill discovery or routing.

The 18 development generations initially passed 13 checks. Before the formal freeze, a numeric-token checker was corrected because sentence-final punctuation caused date false positives. Rechecking the same saved artifacts then passed 18/18, without regeneration; the original ledger results were preserved. Formal inputs and scores use the corrected, frozen checker.

Local validation passed 17 tests, four static skill-bundle checks, installer copy/reinstall and collision checks, and extraction/testing of a candidate archive. These test software behavior and packaging, not personal-style quality. The CI workflow is included but has not run on GitHub.

## Preference evidence still pending

The original pilot prepared an optional private offline review of 12 pairs: three against plain prompts, three against upstream skills and six against deliberately contrasting preferences. The mismatched profile is a constructed negative control, not another person's real style. The selector and random seed were committed separately before style inspection or participant feedback; this auxiliary commitment is distinct from the generation-input freeze.

Ratings separate style fit, clarity and willingness to use, permit ties, and retain unfavorable results. The primary pilot gate uses willingness to use: at least 2/3 wins against each baseline and 4/6 against mismatch. No preference ratings have been collected yet. This one-participant, small synthetic pilot cannot establish population benefit, individual authorship, detector performance or behavior on complex real projects.

The product is intended for general users, with personalization optional. This one participant's approval is not its public quality criterion. A separate [general-use evaluation plan](../evals/GENERAL_USE_PLAN.md) covers the missing evidence and has not run yet. The original frozen pilot protocol and results remain unchanged.

After clarifying the public entry flow, three additional tests passed for an empty generic profile, independent profile selection and exclusion of private profiles from installation (20 local tests in total). These are software-boundary checks, not additional model generations or evidence of multi-user style quality. No participant's preference strings were found in the audited public candidate files.

Aggregate machine-readable counts are in [technical-status.json](technical-status.json). Personal profiles, raw runs, pair mappings and participant notes remain private. General-user quality remains unvalidated; publication requires the owner's approval of the concrete candidate.
