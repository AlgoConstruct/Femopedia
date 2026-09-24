# Femopedia — Accounts and the privacy home

**Date:** 2026-09-24
**Status:** Approved design, ready for implementation planning
**Depends on:** P0 foundation (merged)
**Amends:** a global constraint of the v1 design — see section 6, risk 1

---

## 1. Why this exists, and what changed

The v1 design treated anonymity as the product and an account as a later convenience. That was right about the front door and wrong about the building. The Vision document's central thesis is longitudinal continuity — the teenager who later needs contraception education, the cycle tracker who later investigates PCOS — and continuity is impossible without identity. Device-local history dies with the device.

One assumption is also corrected here. Anonymous is not automatically safer on a shared phone: an anonymous device-local history means anyone who opens the app reads every question she ever asked. A locked account is *more* private in the threat model that actually applies in Nepal, which is a family member or partner picking up the handset.

So: **account as the destination, not the doorway.** She asks her first question without one. When she has history worth keeping, or wants it on a second device, she creates one. Anonymous mode remains a permanent, first-class option rather than a deprecated path.

An account unlocks four things, all of which require identity: history that survives the device, longitudinal tracking, personalisation that compounds, and care artefacts she can show a clinician.

---

## 2. Scope

This slice is **backend only**. The dashboard UI and the app lock are frontend work that lands with the PWA.

### In scope

- `Account` with attached `Identifier` rows — one account, many verified ways in
- Email and password signup with verification
- Google OAuth
- Contact-less accounts: username, password, and a one-time recovery code
- Device binding: login sets `Device.account`; logout unbinds, deletes the device and issues a fresh anonymous token
- The history-merge decision at signup, with the real conversation count shown before she chooses
- Data rights: export everything, delete everything, both provably complete
- Session listing and remote revocation

### Out of scope

- Dashboard screens, app lock, any UI
- Cycle, mood and sleep tracking. The account enables them; it does not contain them
- Care artefacts and clinician summaries
- Facebook OAuth

Facebook is deferred on sequencing grounds, not usage grounds — it is arguably more used in Nepal than Google. Meta requires business verification and app review before granting scopes, which is a multi-week external dependency with a real chance of rejection for a health product. Google's verification is lighter. Adding a provider once `Identifier` exists is small; blocking this slice on a review queue is not.

### Success criteria

She can sign up three ways, sign in on a second device and see the same history, choose whether anonymous history comes with her, export a file containing everything held about her, and delete an account such that nothing referencing her survives. The existing test suite passes unchanged: anonymous use is untouched.

---

## 3. Data model

```
Account
    id                    UUID
    password              Django-hashed; null for OAuth-only accounts
    recovery_code_hash    null unless a contact-less account
    recovery_code_used_at
    created_at

Identifier
    account               FK
    kind                  email | google | username
    value_hash            HMAC-SHA256 with a server pepper — the lookup key
    value_encrypted       the address or provider subject itself
    verified_at           null until proven
    unique (kind, value_hash)

Device  (from P0, extended)
    account               FK, nullable      <- the binding, and the whole design
    bound_at
    label                 derived from user agent, for the session list
```

### Accounts are not `auth.User` rows

Wagtail requires `auth.User` for staff — editors, the clinician, the Nepali reviewer. Putting women's accounts in that same table means one Wagtail permission mistake, or one admin listing view, exposes them. Staff are Django users; users are `Account`s: different tables, different admin, no shared permission surface. Password hashing still reuses Django's hashers — the crypto is borrowed, the model is not.

### Email is a blind index plus ciphertext

Lookup happens on `value_hash`, an HMAC keyed by a server-side pepper; the address itself is encrypted at rest. A dump of a plain email column is a list of women who use a women's health application, which is harmful before anyone signs in as anyone. Because the pepper lives in the environment rather than the database, database access alone yields neither the addresses nor a usable index.

### Anonymous is the same object with a null

`Device.account` being nullable is the entire difference between the two modes. No parallel tables, no guest type, and every endpoint built in P0 continues to work untouched.

### Deletion is immediate and hard

No grace period, per the hard-cascade constraint. The usual argument for a seven-day window is protecting against accidental deletion. The argument against it is stronger here: if she is deleting because someone found the app on her phone, a grace period leaves her data in place during exactly the window in which it can hurt her. Export is offered in the same flow for the accidental case.

---

## 4. Flows

Every request already carries `X-Device-Token`. Authentication never issues a different kind of credential — it changes what the device is bound to. This keeps one authentication path, reuses P0's hardened credential, and makes "anonymous" and "signed in" two states of one object rather than two systems that must agree.

The cost, stated plainly: OAuth libraries such as `django-allauth` assume Django sessions and a `User` model. This design either runs such a library for the handshake alone and translates its result into a device binding, or implements the provider flows directly. That is real integration friction and the one place a second credential scheme would have been easier.

### Signup with email

1. `POST /api/auth/signup/` with `{email, password, bring_history}`.
2. Creates the `Account`, an unverified email `Identifier`, and binds `Device.account`.
3. Sends a verification link. The account is fully usable before verification — friction at this moment costs more than it protects — but an unverified email cannot be used for recovery or for account linking.

### Contact-less signup

1. `POST /api/auth/signup/` with `{username, password, bring_history}`.
2. The server generates a recovery code, stores only its hash, and returns it **once** — the same pattern as the device token, for the same reason.
3. The client must display it and require acknowledgement before continuing. A recovery code she never saw is an account she cannot recover.

### Google

1. The client obtains an authorization code using PKCE.
2. `POST /api/auth/oauth/google/` with `{code, code_verifier}`.
3. The server exchanges the code itself and verifies the ID token's signature, issuer and audience. A client-supplied token is never trusted.
4. Resolution order: an existing `google` identifier signs in; otherwise a **verified** email identifier matching Google's verified email links this provider to that account; otherwise a new account is created.

Step 4's ordering is the duplicate-account fix, and the verification requirement on both sides is what stops an attacker claiming an account by registering someone else's address without proving it.

### Recovery of a forgotten password

For an email account: `POST /api/auth/password-reset/` with the address sends a signed, single-use, time-limited link. The response is identical whether or not the address exists, because a differing response turns the endpoint into an oracle for whether a given woman has an account here.

For a contact-less account: `POST /api/auth/recover/` with `{username, recovery_code}` permits one password change. The code is single-use; completing the flow issues a replacement, returned once, with the same acknowledgement requirement as at signup.

An OAuth-only account has no password to reset. Signing in with the provider again is the recovery path, which is one of the things the provider is doing for her.

### Login, logout, revocation

Login binds this device to the account, and is throttled under its own scope — it is the one endpoint where password guessing is possible.

Logout unbinds the device, deletes the device row, and issues a fresh anonymous token. On a shared phone, logging out must leave an application with no history in it, not a login screen with her data one tap behind it.

`DELETE /api/account/devices/{id}/` does the same to another device. The session list shows label and last-seen so she can drop a handset she no longer has.

### History at signup

1. The client calls `GET /api/devices/history-summary/` and shows the real count — "bring your 14 conversations?" — rather than a vague prompt.
2. `bring_history: true` binds the device as it is; its conversations become the account's.
3. `bring_history: false` **deletes those conversations immediately**, and the interface must say so in plain words.

The alternative — leaving them on the server, unlinked — means health conversations she believes she walked away from remain in the database. If she declined to bring them, the honest reading is that she wants them gone, not orphaned.

---

## 5. Data rights and the API surface

In this slice the dashboard is an **account and privacy home**: who you are, which devices are signed in, what is held, take it, delete it. The health timeline, cycle and mood views that make a dashboard feel like a dashboard depend on tracking that does not exist yet.

**Export** returns the file directly in the response rather than writing it to disk and mailing a link: account, identifiers with the email decrypted, devices, conversations, messages, feedback. No stored artefact means no export file waiting in a bucket to leak, and no link sitting in an inbox someone else may read.

**Delete** requires re-authentication, then hard-cascades across account, identifiers, devices, conversations, messages and feedback.

Re-authentication means, by account type: the current password for an email or contact-less account; a fresh provider sign-in for an OAuth-only account. A valid device token alone is never sufficient — the whole point is that the person holding the unlocked phone may not be her.

### The tension in deletion, stated rather than buried

`SafetyEvent` rows record crisis classifications and the action taken. They are the audit trail proving the safety layer works, and the v1 design makes reviewing them a weekly obligation. They also reference her messages. Deleting her account destroys that evidence; keeping it means data about her survives a deletion she asked for.

Resolution: **the rows are deleted with everything else.** Safety metrics survive because a non-identifying daily aggregate is written at the moment each event occurs — a count per class, with no identifiers, no content and no device reference. The audit capability is preserved without her remaining in the database because the system once classified her as in crisis.

### Endpoints

```
GET    /api/account/                    summary, identifiers, created
GET    /api/account/devices/            session list: label, last seen, current
DELETE /api/account/devices/{id}/       revoke remotely
POST   /api/account/identifiers/        add an email to a contact-less account
DELETE /api/account/identifiers/{id}/   unlink a provider, if another way in remains
POST   /api/account/password/           change; requires the current password
POST   /api/account/export/
POST   /api/account/delete/
```

Removing an identifier is refused when it would leave no way back in. Unlinking Google from an account with no password and no recovery code is a lockout, not a preference.

---

## 6. Testing and risks

### Two tests that keep working as the system grows

- **Export completeness by enumeration.** The test walks Django's model registry for anything referencing `Account` and fails when a model is not covered by the export. Otherwise a later phase adds tracking and the export quietly stops being complete while still passing.
- **Deletion completeness the same way.** After a delete, no row in any table references that account.

### The rest

The existing suite passes unchanged; Google sign-in with a verified email matching an existing verified email links rather than duplicating; an unverified email cannot serve as the merge key; the recovery code is returned once, stored hashed and single-use; `bring_history: false` genuinely deletes; logout leaves a device with empty history; unlinking the last way in is refused; the email column holds no plaintext address; login is throttled.

### Risks

1. **A global constraint is amended, and this should be conscious.** "No personal identifier is ever required to use the API" remains true — anonymous mode is untouched and needs nothing. But "Femopedia holds no personally identifying information" is no longer true of the system as a whole. Later specs inherit the amended form: *no personal identifier is required; identifiers that are volunteered are blind-indexed, encrypted, exportable and deletable.*
2. **Coercion has no technical fix.** Someone standing over her can make her unlock the application and type her password. The app lock and logout-leaves-nothing reduce casual discovery; they do not defeat a person with control over her. Named so that nobody believes otherwise.
3. **The pepper is an operational single point of failure.** Lose it and every email lookup fails: nobody signs in, and the addresses are unrecoverable. It must be backed up separately from the database, or it defeats its own purpose by living beside what it protects.
4. **Deleting `SafetyEvent` rows costs incident forensics.** A crisis handled badly is harder to reconstruct once that account is gone. Accepted deliberately in section 5.
5. **Email deliverability in Nepal.** Verification mail landing in spam breaks signup for people who have no other route in. This needs a real sending service and a verified sending domain, not Django's SMTP default, and it is an external dependency like the clinician.
