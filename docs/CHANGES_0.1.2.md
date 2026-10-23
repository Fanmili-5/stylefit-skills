# 0.1.2 candidate: output contracts

The Luna development diagnostic found two OwnVoice output-contract failures: an extra closing brace made one research response invalid JSON, and an email response renamed the required `artifact` field to `draft`. Their text largely retained the supplied facts, but downstream consumers could not use the required interface. These are observed failures; the specific cause is not established.

One candidate revision changes the return instructions in the three artifact skills. The task's exact output format and field names take precedence over the skills' default artifact-plus-verification layout. Check serialization with a parser when available, and do not claim execution when unavailable. Calibration and verification stay in permitted fields. No case-specific names, facts or expected answers were added.

The initial candidate and development manifest are retained privately. Development answers are not regenerated. The revised candidate is frozen before six held-out tasks. Development and holdout use different tasks, so any difference is not a causal estimate of this patch. A future paired old/new comparison would be needed for that claim.

The profile skill remains 0.1.0. The code, research and email skills are 0.1.2; the bundle is 0.1.2. No detector or authorship capability is added.
