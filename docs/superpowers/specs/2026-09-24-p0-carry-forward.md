# P0 carry-forward

**Date:** 2026-09-24
**Branch:** `design/v1-anonymous-ai-qa`
**Status:** P0 complete. 33 tests passing, ruff clean, final review closed.

Items deliberately deferred during P0, recorded here so the next phase inherits
them rather than rediscovering them. Nothing below blocks P0; each line says why
it was deferred and when it comes due.

## Blocking on a human, not on code

- **Vercel project settings.** Root Directory must be set to `frontend`, and the
  Ignored Build Step to `git diff --quiet HEAD^ HEAD -- frontend/`. The
  repository root moved during P0, so until this is done Vercel builds the wrong
  directory. Guard the command with `git rev-parse HEAD^ >/dev/null 2>&1 || exit 1`,
  because `HEAD^` is absent on a shallow clone or a first build.
- **CI has never been observed green.** `gh` is not installed on the development
  machine, so no run has been watched from the CLI. Confirm in the Actions tab
  for `design/v1-anonymous-ai-qa`, or install `gh`.

## Security and operations, due before any real deployment

- `GET /api/health/deep/` is public and names the four internal datastores,
  including which are down. Free reconnaissance. Either return only an aggregate
  status publicly and the breakdown behind a health token, or restrict by source
  IP at the proxy.
- No `LOGGING` configuration exists. The constraint "the raw token is never
  logged" currently holds by accident — Django's defaults do not log headers and
  gunicorn's access log is off unless enabled. Make it a decision, and settle the
  client-IP policy at the same time: for an anonymity product, the IP is the most
  identifying thing the server touches, and P0 never addressed it.
- `manage.py check --deploy` reports W002, W003, W004 and W008. Nothing sets
  `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_PROXY_SSL_HEADER` or
  `XFrameOptionsMiddleware`, yet the credential rides in a plaintext header and
  the design assumes HTTPS. Set these from environment, silence the genuinely
  inapplicable checks (CSRF, for a header-token API) via `SILENCED_SYSTEM_CHECKS`,
  and add the check to CI.
- `docker-compose.yml` interpolates `${POSTGRES_USER}` and friends with no `:?`
  guard, so `docker compose up` without a root `.env` interpolates empty strings
  and fails obscurely downstream instead of failing fast.
- The running development stack still serves the old `0.0.0.0` bindings until it
  is next recreated. The committed file is correct; the running containers are not.

## Due when P1.5 adds Wagtail

- `INSTALLED_APPS` has no `django.contrib.admin`, `sessions` or `messages`, and
  `MIDDLEWARE` has no `SessionMiddleware` or `AuthenticationMiddleware`. Correct
  for P0, required by Wagtail. Budget for it rather than discovering it.
- `request.user` is now polymorphic. P0 exposes the device explicitly via
  `request.auth`, and application code should read that. Once Wagtail brings real
  staff sessions, `request.user` may be a `Device`, a `User` or `None`.

## Test and code debt, safe to carry

- `test_pgvector_extension_is_available` asserts the extension is installable,
  not created or usable. Correct for P0, since nothing uses pgvector and Chroma is
  the vector store. Strengthen it in whichever phase first enables the extension.
- No test documents the invariant that `/api/health/` and `/api/devices/` must
  stay reachable without a credential. Coverage exists incidentally in
  `test_health.py` and `test_devices.py`; the intent is undocumented.
- `test_devices.py` contains an assertion that cannot fail: a 43-character token
  can never be a substring of its own 64-character hex digest. It guards the
  product's central claim, so it should assert against the serialized row instead.
- `Device.token_hash` carries both `unique=True` and `db_index=True`, redundant on
  Postgres. Free to fix by editing the initial migration; costs a migration later.
- `request.user.last_seen` is stale in-memory for the rest of a request, because
  authentication updates it with a queryset `.update()`. Revisit only if a view
  starts reading it.
- `check_redis` builds a fresh connection pool per probe and never closes it.
  Measured: file descriptors plateau, so it is waste rather than a leak.
- `check_postgres` resets `statement_timeout` to `0` rather than issuing `RESET`,
  which discards a globally or per-role configured default instead of restoring it.
- CI lacks `makemigrations --check --dry-run` — the highest-value missing gate,
  since P1.5 adds many models — plus a `permissions: contents: read` block and a
  `concurrency` group. Every PR branch currently runs the suite twice.
- Historical dependency drift is baked into the lockfile: gunicorn, DRF, psycopg,
  redis and httpx were resolved unbounded before being fenced. Only neo4j was
  rolled back, to match the pinned 5.26 server.
- `.gitignore` does not cover `.env.local` or `.env.production`, which a Vite or
  TanStack frontend commonly uses.

## Process note for P1

Most defects the final review found were in the P0 *plan*, not in its execution:
no throttling, no logging policy despite a "never logged" constraint, upper bounds
applied to Python and Django but not to the other dependencies, `AllowAny` on an
endpoint that discloses topology, no validation on the only client-writable field,
and a README quickstart that was never run. The constraints section was rigorous
about what it thought to be rigorous about and silent elsewhere. P1's plan should
carry an explicit "adversarial inputs and abuse" section alongside its constraints.
