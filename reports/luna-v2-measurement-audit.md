# v2 measurement audit

Recorded after development and before held-out generation. Original task inputs, outputs, checks and scores are preserved. No response is regenerated to improve its score.

The bounded code comparator passed all four reference bundles and rejected seven seeded semantic/interface faults before generation. That verifies sensitivity to those faults, not general equivalence or adequate task difficulty. Development code outputs often preserve the original implementation almost verbatim, so this is a compatibility test with limited refactoring demand.

The frozen text oracle has overstrict, partly unspecified conventions:

- Email amounts require `value` and `role: context` although the public format does not define those nested fields. An `amount` field or a contextual note can express the same facts.
- Local slots require one exact string layout although the task specifies a timezone conversion, not a serialization layout. Equivalent datetime strings and objects are rejected.
- The prose check requires an ISO date substring although natural Chinese and English dates can satisfy the deadline.
- Research source IDs are required inside prose in addition to the requested source map, although that location is not an explicit common task requirement. A supporting-source list can also contain an additional relevant source without being a factual contradiction.

Consequently the all-or-nothing text pass rate is retained as a **frozen strict probe**, not a model-accuracy or skill-benefit measure. It must not headline comparative conclusions. No task-specific post hoc normalization is used to manufacture a corrected success rate. Parsed JSON, required artifact field presence, exact research fact fields and finite code behavior are reported separately; raw prose fidelity still requires review.

The blinded Luna reviewer correctly noticed the invalid JSON but overlooked the email's `draft`/`artifact` mismatch. It also assigned a payment-status binding error to an email ledger whose nested schema was not specified. These demonstrate that model review cannot replace interface checks or settle all interpretation disputes. Its style and adoption ratings are exploratory same-family judgments, not independent human preference data.

All arms receive the same materials and feedback allowance. The task pack explicitly provides current-source precedence and roles, which may simplify the intended conflict-resolution challenge. Multiple fixtures do not create independent task observations. Remaining ceilings or ties will be reported as lack of demonstrated added value.
