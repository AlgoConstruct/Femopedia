# Accounts carry-forward

**Date:** 2026-09-24
**Branch:** `feat/accounts-core`
**Status:** Plan A complete. 153 tests passing, 1 skipped, ruff clean, schema in sync, final review closed.

Items deliberately left, recorded so the next phase inherits them rather than rediscovering them.

## Settle before the conversations phase writes its first row

- **History on login and signup.** Signup's `bring_history` decision was deferred because `Conversation` and `Message` do not exist. Login now does logout-then-login on an already-bound device, so nothing transfers silently — but the deliberate merge flow still has to be built, and it must land before any conversation is written. Two women sharing a handset is the central case.
- **The deletion test's join path.** `test_delete_leaves_nothing_referencing_the_account` filters every walk-discovered model with `.filter(account_id=...)`. That holds for `Device` and `Identifier`. A genuine two-hop model — a `Message` holding only `conversation_id` — will raise `FieldError` rather than fail cleanly. Whoever adds it must give the test a join path, and give `build_export` one too.

## Security follow-ups

- **The `@sensitive_variables` guard only checks one direction.** `tests/test_sensitive_variables_guard.py` proves every name in a decorator is bound somewhere in the function. It cannot catch the opposite and more common shape: a sensitive local that is bound but never added to the decorator, which is what went wrong in `recover`. Four instances of that bug have been found by review, none by a test. A checker that flags plaintext-credential locals absent from the decorator would close it.
- **Password reset still makes a synchronous SMTP call.** No exception escapes and the response is unconditionally 202, but the verified path costs a mail round trip the other two do not, which remains a timing oracle. This closes when a queue arrives; `REDIS_URL` is already wired as a broker. `send_verification_email` in signup has the same shape and should move at the same time.
- **`password_reset`'s identifier lookup is not cost-equalised** across its paths, unlike `login` and `recover`, which now do dummy work on the miss path.
- **`device_revoke`'s self-revocation is not atomic** — it deletes then creates, so a crash between leaves the caller with no device. `logout` shares the pattern. Both should be wrapped, as login's rebind now is.

## Code and test debt

- The `except IntegrityError` in `signup` is file-wide rather than constraint-specific, so a unique violation on anything else in that block would be reported as a duplicate email or username.
- `Account.recovery_code_used_at` is written and never read. Use it or drop it.
- The export omits whether a recovery code exists and when it was last used. Arguably hers under the "everything held about you" framing; the password-hash exclusion is reasoned, this one is not.
- `crypto.py` constructs a new `Fernet` per call. Irrelevant now, worth caching when identifiers are read in bulk.
- `README.md` documents the two new required settings but not the eleven new endpoints.
- `Identifier.is_verified` ships untested.
- `Meta.constraints` is a tuple to satisfy a lint rule; a `ClassVar` annotation is the documented form if the pattern recurs.

## Process note

Three defects in the plan were found by implementers following it faithfully, and a fourth by the final review: the missing `@extend_schema` on every new endpoint, the inline `validated_data` access that made `@sensitive_variables` inert, the single-hop enumeration walk, and the absent throttle scopes on an entire module. The pattern is that the plan specified behaviour carefully and conventions barely at all. A plan for the next phase should state the conventions a new endpoint must satisfy — schema annotation, throttle scope, sensitive-variable handling, permission class — once, at the top, rather than leaving each task to remember them.
