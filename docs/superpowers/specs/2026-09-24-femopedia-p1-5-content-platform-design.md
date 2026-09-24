# Femopedia P1.5 — Content Platform

**Date:** 2026-09-24
**Status:** Approved design, ready for implementation planning
**Implements:** section 6 of `2026-09-23-femopedia-v1-anonymous-ai-qa-design.md`
**Depends on:** P0 foundation (merged)

---

## 1. Scope

Wagtail inside the existing Django project, so that P1's forty entries have a home to be authored and reviewed in, with the review gates enforced by the tool rather than by memory.

This slice is staff-side only. It is independent of the user accounts and dashboard work that follows it, and shares no code with it.

### In scope

- Wagtail 8 integrated into `backend/`, admin served at `/cms/`
- A `cms` Django app defining `KnowledgeEntry` and `BlogPost` page types on a shared abstract base
- `wagtail-localize`, with English as the source locale and Nepali as the translation target
- A two-stage review model: clinical sign-off, and Nepali rewrite review, enforced by Wagtail workflows
- Editor, Clinician and Nepali Reviewer groups, each holding the permissions it needs and nothing more
- The Django contrib apps, middleware and context processors Wagtail requires, which P0 deliberately omitted
- Tests covering the workflow gates, locale linkage, required fields, and — as the release gate — that the device-token API is unchanged by the new middleware

### Out of scope, deliberately

- **No content read API.** P3's retrieval ingest reads the database in-process, and the blog frontend is deferred, so an API now would be a contract with no consumer to validate its shape.
- **No public blog**, no SSR routes, no schema.org markup, no sitemap.
- **No Celery and no publish hook.** The hook described in the v1 design fires a job to re-embed into Chroma and update Neo4j, and neither exists until P3. This slice defines where the hook attaches and leaves it inert.
- **No Chroma or Neo4j writes.**
- **No content authored.** That is P1, and it is gated on securing a clinician reviewer.

### Success criteria

An entry can be created in English, passed through clinical review, translated into Nepali, passed through Nepali rewrite review and clinical confirmation, and published — using three separate accounts holding three different roles. The device-token API passes its full existing suite unchanged.

---

## 2. Content model

Entries are Wagtail **pages**, not snippets. Both types eventually need public URLs and SEO, and `Page` brings revisions, preview, workflow and locale support without additional work.

```
ContentEntryBase (abstract Page)
    summary                        two to three sentences; the direct answer
    body                           RichText; what is actually happening
    when_to_see_a_doctor           RichText, REQUIRED
    tier                           1 | 2 | 3
    clinically_reviewed_by / _at   written by the workflow, not by hand
    nepali_reviewed_by  / _at      written by the workflow, not by hand
    sources                        InlinePanel of Source (title, url, publisher, year)
    topics / conditions / symptoms / life_stages    M2M to snippets

KnowledgeEntry(ContentEntryBase)   what the companion retrieves from
BlogPost(ContentEntryBase)         adds published_at and an author display name
```

### Why `when_to_see_a_doctor` is a field

The v1 design requires that line on every health answer, including reassuring ones, and identifies it as the first thing a clinician checks under scrutiny. As a required model field, an entry cannot be saved without one. As a heading inside a rich-text body, it is forgettable. The same reasoning applies to `summary`: it is the paragraph answer engines cite and the chunk retrieval will favour, so it earns a field rather than being "the first paragraph, probably".

### Locale is not duplicated

The v1 design's `lang` field is dropped. `Page.locale` already carries it, and holding both would let them disagree.

### Graph vocabulary as snippets

`Topic`, `Condition`, `Symptom`, `LifeStage` and `Myth` become Wagtail snippets: translatable, editable in the admin, and taggable onto entries. This gives the domain graph an authoring surface and keeps Postgres authoritative, consistent with the binding constraint that Neo4j holds derived data rebuildable from Postgres.

**Edges are deferred to P3.** `Symptom SUGGESTS Condition`, `Condition RED_FLAG_FOR UrgencyLevel` and `Myth CONTRADICTED_BY Entry` are relationships the Neo4j build consumes, and modelling them without their consumer risks modelling them wrong. P1.5 provides the nodes and the tagging.

The cost of that deferral, stated plainly: entries authored during P1 will be tagged but not related, and someone revisits each one to add relationships when P3 lands.

---

## 3. Workflow, roles and locales

### Locales

`WAGTAIL_I18N_ENABLED = True` with `WAGTAIL_CONTENT_LANGUAGES = [("en", "English"), ("ne", "Nepali")]`, one page tree per locale, linked by `wagtail-localize`.

Wagtail assigns a workflow to a page or a page subtree, not to a locale directly. `wagtail-localize` gives each locale its own root page, so "assigned per locale tree" means the workflow is attached to that locale's root and inherited by its descendants. If the implementation finds the locale roots do not exist as separate subtrees, that assumption is wrong and the assignment mechanism needs rethinking before proceeding.

`LANGUAGE_CODE` moves from `"en-us"` to `"en"`. Wagtail requires it to match a declared content language, and `en-us` does not.

### Two workflows, assigned per locale tree

```
English tree  ->  "Clinical review"
                  Task 1: clinical sign-off           (group: Clinicians)

Nepali tree   ->  "Nepali rewrite review"
                  Task 1: register and terminology    (group: Nepali reviewers)
                  Task 2: clinical confirmation       (group: Clinicians)
```

### Why the Nepali tree carries a clinical task as well

The source-and-translation decision was made on the understanding that Nepali is *rewritten*, not segment-translated, because segment translation produces the euphemistic register the v1 design rules out. But a rewrite is free to change meaning in a way a segment translation is not: "heavy bleeding" rendered into natural Nepali can quietly become a different clinical threshold. Rewritten content needs the same medical eye the English received.

The cost is real and falls on the scarcest person: the clinician touches every entry twice. If that proves to be the bottleneck, the mitigation is to drop task 2 and require the Nepali reviewer to escalate any change beyond register — but that is a policy depending on a person remembering, which is what this design moved into the tool. Start strict; relax only once the clinician time is measured.

### Groups

| Group | Can | Cannot |
| --- | --- | --- |
| Editors | create, edit, submit for moderation | publish |
| Clinicians | approve clinical tasks, comment, edit | create pages |
| Nepali reviewers | approve language tasks, edit Nepali pages | publish English |

Nobody but a superuser publishes directly. Publication is a consequence of a workflow completing, not a button someone is trusted not to press.

### Approval writes back to the page

Workflow approval populates `clinically_reviewed_by/_at` and `nepali_reviewed_by/_at` through a signal, so P3's retrieval filter can select on "tier 1, clinically reviewed" without walking Wagtail's workflow history at query time.

---

## 4. Integration with the P0 backend

### What Wagtail requires that P0 omitted

- `INSTALLED_APPS` gains `django.contrib.admin`, `django.contrib.sessions`, `django.contrib.messages`, the Wagtail apps, `modelcluster`, `taggit` and `wagtail_localize`
- `MIDDLEWARE` gains `SessionMiddleware`, `AuthenticationMiddleware`, `MessageMiddleware`, `CsrfViewMiddleware`, `LocaleMiddleware` and Wagtail's `RedirectMiddleware`
- `TEMPLATES[0]["OPTIONS"]["context_processors"]` is currently empty and must gain the auth, messages and request processors, or the admin will not render
- `MEDIA_ROOT`, `MEDIA_URL`, `DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000`, `WAGTAIL_SITE_NAME`, `WAGTAILADMIN_BASE_URL`

### The risk this slice actually carries

`AuthenticationMiddleware` sets `request.user` to an `AnonymousUser` before DRF sees the request, and P0 set `UNAUTHENTICATED_USER = None` on the assumption that nothing did. DRF wraps the request and should still yield the `Device`; `CsrfViewMiddleware` should be harmless because DRF views are CSRF-exempt. "Should" is doing real work in both sentences. P0 exposed `request.auth` in anticipation of exactly this, and it is the first thing the tests must confirm.

### Version compatibility

Wagtail 8 supports Django 5.2, 6.0 and 6.1, so the P0 pin of `django>=5.2,<6.0` holds. Note for the record that the pin's original justification — that Wagtail supported nothing above 5.2 — was written against Wagtail 7 and no longer applies; the cap is now a choice rather than a constraint.

Wagtail 8's Python support could not be confirmed from the documentation. The project runs Python 3.13. **Verify before writing any models.** If Wagtail 8 requires a newer Python, the fork is to move Python or hold Wagtail at 7.x, and that decision belongs to the human.

`wagtail-localize` is a second pin that must be chosen against the Wagtail version, not independently.

---

## 5. Testing

- **Regression is the release gate.** The full existing suite passes unchanged, plus explicit new tests that `POST /api/devices/`, `GET /api/whoami/` and the 401 path behave identically with the new middleware in place. If the device-token API changes behaviour, this slice is wrong regardless of whether the CMS works.
- The committed `schema.yml` drift test is a free canary: Wagtail adds no DRF endpoints, so any change to that file means something touched the API surface.
- Workflow: a page cannot publish until both of its gates approve; approval populates the reviewed-by fields.
- Validation: an entry without `when_to_see_a_doctor` fails to save.
- Locale: a Nepali translation is created, linked to its English source, and routed through the Nepali workflow rather than the English one.
- Permissions: an Editor cannot publish; a Nepali reviewer cannot approve a clinical task.

---

## 6. Risks

1. **The Wagtail admin is a new credentialed login surface on a product whose premise is anonymity.** It is staff-only and unrelated to devices, but it is a door that did not exist before. This slice serves it at `/cms/`, off the API path, and requires strong passwords. IP restriction or SSO is recorded as a pre-launch item rather than deferred silently.
2. **Wagtail 8 on Python 3.13 is unverified**, as above. Checked before models are written.
3. Wagtail brings a large initial migration set. The first `migrate` is slow, and CI's Postgres service will feel it.
4. `wagtail-localize` compatibility is a second pin to get right.
5. The two-gate workflow doubles clinician load per entry. Measured during P1, not assumed.
