# Frontend architecture

Femopedia uses TanStack Start, React, TypeScript, Tailwind CSS, and shadcn-style UI primitives. Its organization follows the same route/feature/component separation recommended for maintainable Next.js applications without forcing a framework migration.

## Key directories

- `src/routes/`: thin route definitions, route metadata, and page entry points.
- `src/features/marketing/pages/`: page composition with minimal local logic.
- `src/features/marketing/components/`: landing-page sections and marketing-specific UI.
- `src/features/marketing/data/`: typed, reusable visible content.
- `src/features/marketing/seo/`: metadata and structured-data builders.
- `src/components/ui/`: reusable shadcn-style primitives and composed UI.
- `src/components/landing/`: shared landing-page controls.
- `src/lib/`: cross-feature utilities and integrations.
- `public/brand/`: identity, social-sharing, favicon, and manifest assets.

## Conventions

Keep routes thin, colocate feature-specific code, and keep general-purpose UI free of business copy. Structured data must mirror visible page content. Every public route should define a unique title, description, canonical URL, social metadata, crawlable headings, and a sitemap entry.

When more educational content is added, give each topic a descriptive server-rendered URL rather than placing all information behind chat or client-only interactions. Add author/reviewer information, source citations, dates, and medical review policies to health articles.
