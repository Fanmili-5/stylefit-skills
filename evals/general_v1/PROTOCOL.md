# General-use diagnostic v1

Frozen before generation. All cases and profiles are authored synthetic material; no participant profile is loaded. Codex only, using the existing configured service, at most two concurrent CLI generations. No general-user or authorship claim is supported by this diagnostic.

## Allocation

Starting ledger: 99/180 tasks used. One new runtime preflight, 36 development generations (6 domain/language cells x none/compact/expanded x plain/OwnVoice), 6 conflicting-preference generations (3 tasks x 2 methods), then 36 held-out generations with new tasks and opposite generation/rewrite modes. Total new allocation 79, expected ledger 178/180 if completed. At most two remaining tasks may retry failed CLI launches, subject also to the existing four-retry global limit. No successful answer is rerolled. No Claude retries without a changed connection state. Stop on runtime failure or exhausted budget and report missing cells.

The profile-free condition omits the PROFILE section entirely; an empty generic profile is not substituted. Other conditions use the same domain-specific synthetic preference for both methods. Plain and OwnVoice share task constraints, output formatting and profile text. OwnVoice adds its domain skill and relevant references; plain adds only a short generic instruction. No private owner preference file is read.

## Measurements

Content and style are scored separately. Code runs the existing isolated fixture checker, now with exact exception messages specified in these new cases. Text retains quantities, selected markers and protected spans; string checks are not semantic proof. A review of all new text artifacts must assess missing qualifications, reversals, added facts and commitment/deadline changes separately.

The predeclared style probes are narrow instruction-adherence measurements:

- Compact code: at least one short internal name (at most 4 letters excluding underscores), at least one list comprehension, no more than one comment.
- Expanded code: at least two descriptive internal names (at least 8 letters excluding underscores), at least three assignment statements, at least one comment. Comment usefulness remains a manual review item.
- Compact research: result quantity precedes sample size; three to six sentences; longest sentence at most 35 English words or 90 Chinese characters; one paragraph.
- Expanded research: sample size precedes result quantity; one or two sentences; one paragraph.
- Compact email: one paragraph, no greeting or thanks.
- Expanded email: greeting and thanks/closing, at least three paragraphs.
- No profile: content checks pass, no questionnaire/onboarding request or unsupported claim about the user's habits. This does not measure naturalness; that remains a review judgment.
- Conflicting preferences: task contract wins. Do not reward compliance with the invalid preference.

Report complete numerators/denominators, failures, ties where applicable, domain/language and method. These deliberately check observable style differences, not overall quality, personal identity or the skill's advantage over plain instructions. A pair distinguishes a measured preference only when both contrasted outputs pass content and their respective style checks; identical artifacts are reported.

## Development and held-out separation

Freeze cases, checker, runner and initial skill snapshots before development. Review development/conflict outputs, then make only changes supported by those findings. Preserve the exact initial skill snapshot privately. Before held-out generation, freeze the final candidate and any declared fixes; do not inspect held-out generations until that batch completes. No new checker tuned to generated wording may silently replace these v1 scores. Any checker coverage gap is disclosed with a separately labelled sensitivity/manual review.

The prior single-participant protocol and results remain intact. If current skills are changed after development, old inputs are verified against their saved snapshot, rather than pretending the current tree still matches the old freeze. All raw generations, prompts and runtime configuration hashes remain private; publish only synthetic inputs, code, aggregate results and authorized synthetic examples. Actual host skill routing and multi-user/stateful sessions are outside this text-only CLI test.
