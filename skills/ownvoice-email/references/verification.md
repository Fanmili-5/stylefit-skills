# Executable delivery checks

The optional helper is installed by the suite installer with `--with-tools`. Use the script path relative to this skill, not a hard-coded checkout path:

    python3 <skill-directory>/scripts/verify.py --artifact draft.json --schema schema.json --constraints constraints.json --report checks.json

Schema and constraints flags are optional; use only contracts explicitly supplied or clearly established by the task. Do not derive expected facts solely from your candidate. Ordinary prose does not need to become JSON; without a structured contract the helper only checks nonempty text and reports its gaps.

The verifier never rewrites the artifact. Exit 0 means the declared checks passed, 1 means a candidate failed, and 2 means an invalid contract/missing environment prevented validation. A required not_run check blocks a verified delivery. Missing helper setup must be reported, never bypassed with a success claim.

Read the JSON report. Revise once using exact errors, run checks on that revision, and keep the final failure visible if it persists. Do not invent a parser execution or add fields that violate the user's schema. Temporary calibration/check material stays separate when the output format has no place for it.

Schema checking protects shape, not truth. Explicit structured facts can be checked using equal, date, source_ids and unit_conversion assertions. Free-form text must also be reviewed against the actual source/current brief; identify that as model/human review with evidence, not mechanical proof. Superseded records, unknown values and actor/deadline bindings need direct inspection. Never create a passed review attestation merely because a ledger parsed.
