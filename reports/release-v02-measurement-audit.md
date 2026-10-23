# 0.2 native evidence audit

The initial native-evidence parser marked implicit research as `no_observed_skill_read`. The saved tool output contained the complete research SKILL.md, but the same shell command ended with a failing `rg` against a wrong relative directory. The parser incorrectly used the shell chain's final exit code to discard the successful earlier read.

The corrected parser requires both the relevant skill path in the executed command and its actual complete contents in the captured tool output. Merely mentioning a path, a failed cat or partial contents does not pass. Added positive and negative unit controls cover these cases. This is an evidence-parser correction, not a rerun of a failed model answer or a change to a held-out task.

The original assessment is retained privately beside the re-assessment. Original commands, nonzero shell exit, outputs and model artifacts are unchanged; no extra model call is used for this correction. Installed helper execution and artifact/report hashes remain separate requirements. Formal held-out generation and its frozen inputs are unaffected.

## Material-flag validity audit

The first calendar-email review produced seven flags: four for OwnVoice, two for plain prompting and one for the checklist. These original flags, fidelity ratings and artifacts remain unchanged. One additional Luna call, counted in the necessary-review reserve, reviewed all seven flags under fresh anonymous labels against the original task, schema, brief and full outputs. No artifact was regenerated.

It classified all four OwnVoice flags and the checklist flag as unsupported: `payment_date: null` was preserved in the ledger, with no explicit requirement to repeat that unknown value in the body; the request to send a template in an email from Taylor was consistent with Taylor as the recipient recorded in the ledger, without a requirement to repeat the sender's name. For plain prompting it upheld the missing not-approved status and left the omitted meeting slots unclear. Supported and unclear flags continue to count as unresolved.

This is a post-hoc scoring audit, not a pre-registered independent quality result or human evaluation. The original raw flag counts and ratings are published beside unresolved counts. The audit reported no additional errors; its empty additional-errors list is not interpreted as proof of an exhaustive second review. It resolves the stated flags only. The release criterion remains no *unresolved material* OwnVoice source error, rather than erasing initial flags or lowering the style/contract thresholds.
