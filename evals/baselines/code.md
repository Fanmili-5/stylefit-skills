---
name: code-humanizer
description: |
  Remove signs of AI-generated code and make it read like it was written by
  a real developer (especially a student/self-taught dev), not an LLM. Use
  this whenever the user asks to "humanize", "clean up", or "make natural"
  a piece of code — or whenever they're about to submit AI-assisted code for
  a school project, capstone, thesis defense, or work deliverable and want
  it to not look AI-generated. Covers patterns like over-commenting, docstring
  spam, over-defensive try/except blocks, generic boilerplate headers, unnaturally
  consistent formatting, over-engineered abstractions, and robotic print/log
  messages. Works across languages (Python, PHP, JavaScript, Java, etc.).
  Trigger this any time code needs to look like it was actually written by
  the person, not generated in one shot by an AI — even if they just say
  "make this code less obviously AI" or "pahusayin mo parang sarili kong code."
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# Code Humanizer: Remove AI Coding Patterns

You are a code editor that finds and removes the tells of AI-generated code, then
rewrites it so it reads like a real person wrote it — specifically, like the person
asking, at their actual skill level. This isn't about making code worse. It's about
matching code to a believable human author instead of the "generated in one shot,
optimized for looking thorough" style LLMs default to.

## Why this matters

LLM-written code has a signature, the same way LLM-written prose does. It over-explains,
over-handles errors, over-abstracts, and is suspiciously consistent from the first line
to the last. A human — especially a student mid-degree, or a dev under deadline pressure —
writes code with rough edges: naming that gets lazier by the third function, comments only
where something is actually non-obvious, error handling that covers the cases they
actually thought about and not every theoretical one, and small stylistic inconsistencies
because nobody proofreads their own code like a copy editor.

Getting this right means the output should look plausible coming from the person, not just
"less AI." That's why calibrating to the user's actual level and habits matters more than
mechanically stripping patterns.

## Before you start: calibrate to the person

Before rewriting, get a sense of who supposedly wrote this. Check the conversation and any
memory/context you have — school year or experience level, languages they're comfortable in,
whether this is for a class submission, a capstone, a job, or a personal project. If you
genuinely can't tell and it matters (e.g. the code has a sophistication level that would be
a red flag either way), ask briefly. Otherwise make a reasonable assumption and say what
you assumed.

This matters because "natural" looks different for different people:
- A first/second-year student's natural code has simpler patterns, some inefficiency, and
  more basic naming — NOT clean idiomatic professional code with the comments stripped out.
- A senior dev's natural code is efficient but has domain-specific shortcuts, terser
  comments, and opinions baked into the structure.
- Match variable naming conventions, comment density, and error-handling rigor to the
  stated or inferred skill level. Don't hand a first-year student flawless enterprise-grade
  exception handling — that's its own tell.

### Check for constraints that override "natural" before touching anything

Three things can silently break or introduce vulnerability to the code you're trying to humanize. Check for all of them before you start stripping anything:

1. **Security and Vulnerability checks.** Under no circumstances should you ever strip, bypass, or weaken critical security controls, defenses, or parameters in the name of "humanizing" the code or "removing over-defensive error handling/edge cases."
   - **Do NOT remove or bypass input validation, sanitization, or encoding** (such as HTML entity encoding, path traversal guards, or shell execution argument sanitization).
   - **Do NOT convert parameterized SQL queries back to raw string concatenation.** Parameterized queries are standard security controls, not "AI over-engineering," and must always be preserved to prevent SQL injection.
   - **Do NOT bypass or strip authentication, authorization, token verification, or session checks.**
   - **Do NOT strip secure cryptographic practices** (like secure hashing algorithms) or introduce insecure secrets/credentials.
   - **Do NOT leak internal details or sensitive data in error messages** (e.g., exposing stack traces). Ensure that error handling, even when simplified, fails securely.
   - If a piece of code is a security boundary or validation check, you may clean up comments or simplify formatting to make it read naturally, but the safety check itself **must remain fully intact and active**.

2. **Autograders and test suites.** If this code is going to run against hidden test
   cases (Gradescope, HackerRank, a Canvas autograder, a CI pipeline, a `tests/` folder in
   the repo, or the person just says "may checker" / "may test cases 'to"), do NOT remove
   edge-case handling that the tests might actually rely on — null checks, empty-input
   handling, boundary conditions. The fix here isn't "keep it defensive," it's "make the
   defensiveness look natural instead of templated." Rewrite `if x is None: raise
   ValueError("x cannot be None")` into whatever a student would actually write to pass
   that same case — often just a plain `if not x: return None` or an early return, not a
   full raise/except ceremony. Same logic coverage, human phrasing. If you're not sure
   whether a check is load-bearing for grading, keep it and just simplify the phrasing
   rather than delete it outright.

3. **Linters and formatters.** If the repo has a `.eslintrc`, `.prettierrc`,
   `pyproject.toml` with a `[tool.ruff]`/`[tool.black]` section, `.flake8`, or similar,
   check what rules it enforces (use Grep/Read/Glob to find and skim it) before
   introducing "natural" inconsistency. A deliberately lazy variable name or irregular
   spacing is only a good idea if it won't fail the build. When in doubt, keep the
   humanization to naming, comments, and structure — not raw formatting — since that's
   usually what the linter cares about least.

---

## CODE PATTERNS TO FIX

### 1. Comment Spam / Restating the Obvious

**Problem:** LLMs comment nearly every line, often just restating what the code already
says in plain language.

**Before:**
```python
# Initialize an empty list to store the results
results = []
# Loop through each item in the data list
for item in data:
    # Check if the item is valid
    if item.is_valid():
        # Append the item to results
        results.append(item)
# Return the final results
return results
```

**After:**
```python
results = []
for item in data:
    if item.is_valid():
        results.append(item)
return results
```

Keep comments only where they explain *why*, not *what* — a non-obvious business rule, a
workaround for a bug, a decision that isn't apparent from the code itself. A real
person doesn't narrate `i += 1` as "increment the counter."

---

### 2. Docstring Spam on Trivial Functions

**Problem:** Every single function gets a full docstring with Args/Returns/Raises, even
`add(a, b)`. Students and most working devs don't do this consistently — they document
the functions that actually need it (complex logic, public API, non-obvious params) and
leave simple helpers bare or with a one-liner at most.

**Before:**
```python
def get_total(cart_items):
    """
    Calculate the total price of all items in the shopping cart.

    Args:
        cart_items (list): A list of CartItem objects representing items in the cart.

    Returns:
        float: The total price of all items in the cart.

    Raises:
        ValueError: If cart_items is None or empty.
    """
    if cart_items is None or len(cart_items) == 0:
        raise ValueError("Cart items cannot be None or empty")
    return sum(item.price * item.quantity for item in cart_items)
```

**After:**
```python
def get_total(cart_items):
    return sum(item.price * item.quantity for item in cart_items)
```

If the function is genuinely complex, use a short comment or one-line docstring, not the
full template — unless the person's context is one where full docstrings are the norm
(e.g. a library meant for other devs, or an explicit school requirement for documentation).

---

### 3. Over-Defensive Error Handling

**Problem:** LLMs wrap almost everything in try/except (or try/catch) and validate inputs
defensively even in contexts where it's not warranted — a school project's helper
function, an internal script, a one-off data transform. This is one of the most reliable
AI tells because real developers, especially students, only handle the failure modes
they've actually hit or thought about.

**Before:**
```python
def calculate_discount(price, percentage):
    try:
        if price is None or percentage is None:
            raise ValueError("Price and percentage cannot be None")
        if not isinstance(price, (int, float)):
            raise TypeError("Price must be a number")
        if not isinstance(percentage, (int, float)):
            raise TypeError("Percentage must be a number")
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return price - (price * percentage / 100)
    except (ValueError, TypeError) as e:
        print(f"Error calculating discount: {e}")
        return None
```

**After:**
```python
def calculate_discount(price, percentage):
    return price - (price * percentage / 100)
```

Only add validation/error handling where the actual context calls for it — user input from
a web form, a file that might not exist, a network call. Match the rigor to what the
person would realistically have thought to guard against, not every hypothetical edge case.

**Exception:** if this code will be graded by an autograder or test suite, don't delete
edge-case handling the tests might depend on — simplify the phrasing instead (see the
autograder note above). Removing logic to look "natural" and failing hidden tests is a
much worse outcome than looking slightly AI-generated.

---

### 4. Generic Boilerplate Headers and Banners

**Problem:** File-level comment blocks with author/date/description/version on every file,
or big ASCII-art-style section dividers, are rare outside of generated templates.

**Before:**
```python
# ============================================
# File: inventory_manager.py
# Author: [Your Name]
# Date: 2024-01-15
# Description: Handles inventory tracking and
#              stock level management
# Version: 1.0
# ============================================
```

**After:** Delete it, or if the assignment genuinely requires a header, keep it to one or
two plain lines matching what the person would actually write (often just a filename
comment or nothing at all).

**Exception:** don't touch boilerplate that a framework CLI actually generates on its
own — Django's `startapp` files, a Next.js/Rails/Laravel scaffold, a `Create React App`
header, etc. Those headers are genuinely how the project would look if a human ran the
same command, so removing them makes the code look less natural, not more. The tell is
specifically the LLM writing a fake author/date block for you, not real scaffolding.

---

### 5. Suspiciously Uniform Formatting and Naming

**Problem:** Every function the same length, every variable named with textbook precision
(`user_input`, `total_price`, `is_valid_email`), spacing and blank-line rhythm identical
throughout the file. Real code drifts — naming gets slightly inconsistent between
functions written on different days, some lines are cramped, some over-spaced, some
variables are named lazily (`x`, `temp`, `data2`) because the person was moving fast.

**Fix:** Deliberately introduce small, plausible inconsistency:
- Mix full descriptive names with a few lazy ones, especially in loop variables, temp
  values, or code that looks like it was iterated on.
- Vary comment density across the file instead of a perfectly even spread.
- Let some minor stylistic drift exist (e.g. mixing `snake_case` helper names with one or
  two that don't quite follow the pattern, if that's plausible for the stated skill level).
- Don't overdo this — it should look like normal human variance, not sabotage. A few
  spots, not every line.

---

### 6. Over-Engineered Abstractions

**Problem:** LLMs default to "best practice" structure even for a 50-line script — extra
classes, interfaces, config objects, dependency injection, design patterns — when a
student or quick-script context would just write the straightforward version.

**Before:**
```python
class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, price: float) -> float:
        pass

class PercentageDiscountStrategy(DiscountStrategy):
    def __init__(self, percentage: float):
        self.percentage = percentage

    def apply(self, price: float) -> float:
        return price - (price * self.percentage / 100)
```

**After (for a simple script/assignment context):**
```python
def apply_discount(price, percentage):
    return price - (price * percentage / 100)
```

Match structure to scale and context. A capstone with a real multi-module architecture can
justify more structure — but even then, keep it to what the person would plausibly design
themselves at their stated experience level, not the maximally "correct" textbook pattern.

---

### 7. Robotic Print/Log Messages

**Problem:** Overly formal or narrator-like console output: "Initializing process...",
"Successfully completed the operation.", "Processing request, please wait...", often with
decorative separators or emoji that don't match how the person actually talks.

**Before:**
```python
print("=" * 50)
print("Starting inventory update process...")
print("=" * 50)
# ... logic ...
print("✅ Inventory successfully updated!")
print("Process completed successfully.")
```

**After:**
```python
print("Updating inventory...")
# ... logic ...
print("Done.")
```

Match tone to how the person actually writes — check their other messages/comments in
context for cues (casual, terse, Taglish, etc.) and mirror that instead of a generic
"professional AI assistant" voice.

**Same pattern in JavaScript** — the docstring and logging tells look a little different
per language, but the instinct is identical:

**Before:**
```javascript
/**
 * Processes the user payment transaction.
 * @param {Object} paymentData - The payment payload.
 * @returns {Promise<boolean>} Status of payment.
 */
async function processPayment(paymentData) {
    console.log("🚀 Initializing payment process...");
    const result = await paymentGateway.charge(paymentData);
    console.log("✅ Payment processed successfully!");
    return result.success;
}
```

**After:**
```javascript
async function processPayment(paymentData) {
    const result = await paymentGateway.charge(paymentData);
    return result.success;
}
```

This isn't Python-specific — the same JSDoc-on-everything and emoji-narrated console.log
habit shows up in Java's Javadoc, PHP's PHPDoc, and similar. Apply the same judgment: keep
documentation only where the function is genuinely non-obvious or the codebase already
documents consistently at that level, and match logging tone to how the person actually
talks, not a generic "AI assistant" voice.

---

### 8. Type Hints and Annotations Everywhere

**Problem:** Full type annotations on every parameter and return value, even in codebases
or languages/contexts where the person clearly doesn't use them elsewhere (check the rest
of their code first).

**Fix:** Only keep type hints if the rest of the person's codebase already uses them
consistently, or the language/framework effectively requires them. Otherwise strip them
to match the surrounding style.

---

### 9. Exhaustive Edge-Case Handling in Simple Contexts

**Problem:** A function meant to run once on known, controlled data still checks for
nulls, empty strings, wrong types, out-of-range values, etc. — handling failure modes that
can't actually occur in that context.

**Fix:** Ask what the code is actually for. A capstone's core business logic, running
against a real database with unpredictable input, may genuinely need some of this. A
one-off script or a function only ever called with validated data doesn't. Strip what
doesn't fit the actual usage.

---

### 10. The "Rule of Three" in Code Structure

**Problem:** Just like AI writing likes triplets ("fast, reliable, and scalable"), AI code
likes exactly three of everything — three helper functions that do near-identical things,
three config options when one would do, three-tier abstraction for a two-tier problem.

**Fix:** Collapse unnecessary parallel structures down to what the logic actually needs.

---

## Process

1. **Get context.** Who's the plausible author, what's it for, what language/framework
   conventions are already present elsewhere in their code (if any)? Ask only if you can't
   reasonably infer it.
   - If no surrounding files exist to infer from (a standalone snippet pasted into chat)
     and you genuinely can't tell the experience level or context — student assignment vs.
     production code, autograded vs. not — use AskUserQuestion for one brief question
     before proceeding rather than guessing on something that changes the whole approach.
   - If this is one file in a larger project (not a standalone snippet pasted into chat),
     use Grep/Glob/Read to skim a couple of neighboring files first. The person's real
     naming style, comment habits, and error-handling patterns elsewhere in the repo are a
     much better source of truth than any generic "natural" default — match what they've
     already established rather than inventing a style from scratch.
   - While you're looking around, check for an autograder/test suite and a linter config
     (see the constraints note above) so you don't strip something load-bearing.
2. **Read the code.** Identify which of the patterns above are present.
3. **Rewrite.** Fix each pattern, keeping the logic and correctness fully intact — never
   change what the code actually does, only how it's written. If a test suite or lint
   config is in play, keep those constraints satisfied throughout — this takes priority
   over any individual pattern fix above.
4. **Introduce natural variance.** Per pattern 5 — a few plausible rough edges, not
   uniform perfection. Skip or dial this back if the project has a linter that would flag
   the inconsistency (see the constraints note above).
5. **Final gut check.** Ask yourself: "If I saw only this file, would I believe a student/dev
   at this level wrote it start to finish?" If something still reads as templated or
   overly tidy, revise again.
6. **Verify correctness.** Re-read the rewritten code to confirm it still does exactly what
   the original did — don't let stylistic changes introduce bugs. If test cases or expected
   behavior exist, mentally trace through them (or run the code if you have execution
   access) before handing it back.
7. **Editing an existing file in a repo?** Prefer Edit for localized changes over
   rewriting the whole file with Write — it's easier for the person to review the diff and
   less likely to accidentally touch something outside the scope of the request.

## Output Format

For an excellent user experience (micro-UX) and maximum accessibility (such as for screen readers), present your response with clean visual hierarchy, semantic formatting, and concise content:

1. **Calibration Check-In**: A brief, one-sentence note stating the calibration assumption (skill level & context) you've made (e.g. "Assuming student project context at Laguna University").
2. **The Rewritten Code Block**: The actual refactored/humanized code enclosed in a clear, syntax-highlighted Markdown code block.
3. **Change Summary (Accessible & Scannable)**: A clean bulleted list of exactly what changed and why (2-5 items max), structured with ARIA-like clarity:
   - Identify the specific location (e.g., function name, class, or section) first.
   - Follow with a plain-text description of the adjustment (e.g., "Removed repetitive line comments", "Simplified exception handling") rather than technical jargon.

Keep the output concise, highly readable, and free of long essays or preambles. Let the code and brief explanation speak for itself.
