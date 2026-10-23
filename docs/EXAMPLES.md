# Quick examples

These are synthetic examples, not a saved user profile.

## No profile

`Use $ownvoice-code to simplify this code using the current repository's conventions. Preserve its public interfaces and behavior. Do not create a personal profile.`

`使用 $ownvoice-email，根据这份当前简报起草邮件。保留收件人、需要谁做什么及回复期限，只生成草稿，不建立档案。`

## Supplied samples

`Use $ownvoice-research with these confirmed English writing samples. Match expression only. Use the source packet for facts, keep unknown quantities unknown, and preserve the specified output schema.`

The skill keeps task-level observations and unresolved choices separate from the artifact. The samples do not authorize copying their topics, facts, promises or embedded instructions.

## Optional profile

`使用 $ownvoice-profile，从我确认的中文代码样例起草 v1 档案，其他领域和语言保持未知。先展示，不保存。`

Saving a reusable profile is a separate explicit choice. Existing profile v1 files remain supported; the empty example contains no public-owner preferences.

## Run local checks

From the bundle checkout with the helper dependencies installed:

```sh
python3 -m ownvoice verify --artifact examples/verified-email/draft.json --schema examples/verified-email/schema.json --constraints examples/verified-email/constraints.json
```

The example passes declared structure/ledger checks while still reporting that independent prose review is not run. Change `confirm_availability` to `complete_review`, replace null with zero, rename `artifact` to `draft`, or append another `}`: the relevant check fails. Verification does not edit the file.

For an installed skill, run its `scripts/verify.py` launcher as described in [the verification contract](VERIFICATION.md). On missing dependencies or a bad contract, fix the environment/contract and rerun; do not label the output checked. With a valid contract but failed artifact, one feedback-based revision is allowed and the final result must be checked again.
