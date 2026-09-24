# Femopedia — Interface internationalisation

**Date:** 2026-09-24
**Status:** Approved design. Implemented alongside the PWA (P5); specified now so P5 does not invent it ad hoc.
**Relates to:** `2026-09-24-femopedia-p1-5-content-platform-design.md` (content i18n, a separate system)

---

## 1. Two systems, not one

Femopedia has two translation problems and they share nothing:

- **Content** — knowledge entries and blog posts. Long-form, clinician-reviewed, authored in English and rewritten in Nepali. Handled by Wagtail; see the P1.5 design.
- **Interface** — buttons, navigation, form labels, validation messages, empty states, onboarding copy, and the fixed crisis-breakout text. Short strings, written by whoever builds the screen, changed often.

This document covers the second. Nothing here applies to entry content, and the two must not be merged: editorial review gates belong on content, and would only obstruct a button label.

---

## 2. Requirements

- A Nepali speaker who is not an engineer can correct awkward interface wording without a deployment. Register is the thing most likely to be wrong and most visible to the reader.
- Every string is discoverable whether or not its screen has ever rendered. A crisis screen's copy must be translated before anyone sees the crisis screen.
- Server-rendered HTML is already in the reader's language. No flash of English, and no English markup served to a crawler on a Nepali URL.
- Plurals and interpolation work, because "2 दिन अघि" and "Logged {n} entries" are ordinary cases, not edge cases.
- Dates read in the calendar the reader actually uses.

---

## 3. Design

### Runtime

A real i18n library rather than a bespoke key-to-string map: **i18next** with `react-i18next`, integrated with TanStack Start's SSR so the server renders in the request's locale. The alternative considered was Lingui, which is leaner and compiles messages at build time; i18next is chosen for its maturity around runtime-loaded catalogues, which this design needs because translations come from the database rather than from the bundle.

A bespoke map was rejected for one concrete reason: it cannot do plurals or interpolation, and rebuilding either badly is worse than taking the dependency.

### Keys

Keys are namespaced by screen or feature, and map to **strings, not blocks of markup**:

```tsx
t("chat.input.placeholder")
t("chat.sources.count", { count: n })
```

Markup stays in the component. A key that wraps a `<div>` containing nested links or emphasis forces the translation to carry HTML, which is both fragile and an injection surface. Where a sentence genuinely needs inline markup, i18next's `<Trans>` component handles it without putting HTML in the database.

### Extraction is static, not by scanning the DOM

Keys are extracted from source at build time with `i18next-parser`. A runtime DOM scan only finds strings in components that happened to render, which silently omits error states, modals, empty states and the crisis screen — precisely the copy whose absence hurts most. Static extraction finds every key whether or not it ever rendered.

Extraction produces a JSON catalogue of keys and English defaults, committed to the repository. A CI check fails when the committed catalogue drifts from what the source produces, exactly as `schema.yml` is guarded today.

### Translations live in Postgres and are edited in the admin

This is the part of the original proposal that carries the design.

```
UIMessage
    key            unique, dotted namespace
    default_text   English, synced from the extracted catalogue
    context        optional note for the translator: where this appears
    is_obsolete    set when a key disappears from the catalogue

UITranslation
    message        FK to UIMessage
    locale         "ne"
    text
    status         machine_draft | human_reviewed
    reviewed_by / reviewed_at
```

A management command imports the extracted catalogue: new keys are created, changed English defaults mark their translations for re-review, and keys no longer present are marked obsolete rather than deleted, so a rename does not silently discard work.

A Wagtail admin section lists keys with their English text, their Nepali text and status, filterable by "untranslated" and "needs re-review".

### AI drafts, a human signs off

A command sends untranslated strings to the model already used elsewhere in the system, with a prompt carrying the same register instruction the content guidelines use: natural Nepali, direct terms, no euphemism. Output is stored as `machine_draft` and **never served as-is** — the UI falls back to English until a human marks a string `human_reviewed`. A machine draft shown to a woman in a crisis screen is worse than English she can at least recognise as foreign.

### Serving

Reviewed translations are exported to JSON catalogues, cached, and loaded by the SSR renderer per request locale. The database is the editing surface; the served artefact is a flat file. This keeps rendering off the database path and makes the served state explicit and rollback-able.

---

## 4. Dates: Bikram Sambat

**Storage never changes.** All timestamps are stored UTC Gregorian. This is a display concern only.

**Display is locale-driven with an override:** the Nepali locale renders Bikram Sambat, English renders Gregorian, and a user setting overrides either. Urban users may think in Gregorian, diaspora users certainly do, and a summary a clinician reads may need either.

BS conversion is table-driven — month lengths vary per year with no closed formula — so it requires a conversion library with lookup tables, pinned, with its supported year range checked against the range the product needs. A date outside the table's range must raise rather than silently produce a wrong date; a wrong date in a cycle-tracking health product is a clinical error, not a formatting bug.

Relative dates ("3 days ago") go through i18next's plural rules for the active locale, not through string concatenation.

---

## 5. Testing

- Extraction: the committed catalogue matches what the source produces; CI fails on drift.
- Import: a new key is created, a changed English default marks its translation for re-review, and a removed key is marked obsolete rather than deleted.
- Fallback: a string with only a `machine_draft` translation renders in English, not in the draft.
- SSR: a Nepali request returns Nepali in the server-rendered HTML, with no client-side swap.
- Plurals: Nepali plural forms resolve correctly at 0, 1 and n.
- Calendar: known Gregorian and BS pairs convert both ways; a date outside the conversion table's range raises.

---

## 6. Risks

1. **Machine drafts leaking into the UI** would put unreviewed Nepali in front of a vulnerable reader. The English fallback is the control, and its test is not optional.
2. **BS conversion table range.** Silent wrongness is the failure mode, which is why out-of-range must raise.
3. **Two sources of truth for English** — the source code carries defaults and `UIMessage.default_text` mirrors them. The import command is what keeps them honest, and the CI drift check is what proves it.
4. **Scope creep into content.** Interface strings must not become a route for publishing health content that bypasses clinical review. The admin section is separate, and no interface string should contain medical guidance.
