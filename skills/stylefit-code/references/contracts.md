# Code contract
Preserve required names and keyword parameters, defaults, return types, exception behavior, logging, random draws, dtype, shape, axis/reduction order, preprocessing and saved parameter names.
None checks and truthiness checks are different. Equality to True and truthiness are different. Error logs and catch-and-return are observable behavior.
A single-use class can represent a real layer, cache, or serialization boundary. Judge purpose rather than call count.
Respect real task constraints. Do not retrain models, inspect held-out labels, or change dependencies merely for style.
A before/after static checker can flag declared API changes; dynamic exports, descriptors, reflection and framework behavior require project-specific verification.
