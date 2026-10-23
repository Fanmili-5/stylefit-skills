# StyleFit development
Use Chinese with the project owner. Keep this project separate from coursework.
Do not claim authorship detection, universal style matching, or behavioral equivalence from static checks.
Profiles, raw runs, blind mappings and personal feedback stay under .local/ and are never published by default.
Evaluation generation cap is 180 CLI tasks including failed tasks and retries. Never reset the ledger to gain budget.
On 2026-10-22, after those 180 tasks were exhausted, the owner explicitly authorized 60 additional tasks for the complex diagnostic. The lifetime ceiling is now 240, with at most 60 new tasks under the luna-v2 stages. Count generation, model grading, failures and retries. All subsequent experiment generation and model grading must explicitly select gpt-6-luna; do not inherit another default or fall back to another model. Preserve the original ledger and results.
Freeze evaluation inputs before the main run. Do not tune on the formal results.
Do not publish to GitHub without approval of a concrete release candidate.
Run python3 -m unittest discover -s tests before accepting code changes.
On 2026-10-23 the owner approved implementation of the OwnVoice 0.2 plan and 120 additional CLI tasks, all explicitly gpt-6-luna / medium, including preflights, generation, revisions, grading, host tests, failures and retries. Preserve the 239 existing jobs. The ownvoice-v02 stage has an independent cap of 120 and a lifetime ceiling of 359; do not spend the unused luna-v2 reservation to enlarge this round. Release requires all 12 OwnVoice held-out outputs to pass declared contracts, at least 5/6 paired-style matches with coverage in every domain, no unresolved material source errors, and all eight native Codex tests to pass. Otherwise retain a release candidate and report the failed gate. Keep formal inputs frozen and never tune on held-out outputs.
