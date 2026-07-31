import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { Blobs } from "@/components/landing/Blobs";
import { Hero } from "@/components/landing/Hero";
import { Nav } from "@/components/landing/Nav";
import { TrustedBy } from "@/components/landing/TrustedBy";

const Features = lazy(() =>
  import("@/components/landing/Features").then((m) => ({ default: m.Features })),
);
const HowItWorks = lazy(() =>
  import("@/components/landing/HowItWorks").then((m) => ({ default: m.HowItWorks })),
);
const JourneyTimeline = lazy(() =>
  import("@/components/landing/JourneyTimeline").then((m) => ({ default: m.JourneyTimeline })),
);
const CompanionShowcase = lazy(() =>
  import("@/components/landing/CompanionShowcase").then((m) => ({ default: m.CompanionShowcase })),
);
const Personalization = lazy(() =>
  import("@/components/landing/Personalization").then((m) => ({ default: m.Personalization })),
);
const Privacy = lazy(() =>
  import("@/components/landing/Privacy").then((m) => ({ default: m.Privacy })),
);
const Testimonials = lazy(() =>
  import("@/components/landing/Testimonials").then((m) => ({ default: m.Testimonials })),
);
const Faq = lazy(() => import("@/components/landing/Faq").then((m) => ({ default: m.Faq })));
const Waitlist = lazy(() =>
  import("@/components/landing/Waitlist").then((m) => ({ default: m.Waitlist })),
);
const Footer = lazy(() =>
  import("@/components/landing/Footer").then((m) => ({ default: m.Footer })),
);

const title = "Aria — AI Companion for Women's Health";
const description =
  "Aria is an AI companion supporting your physical, emotional and mental wellbeing through every stage of womanhood—cycle, pregnancy, postpartum, childcare and menopause.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
    scripts: [
      {
        type: "application/ld+json",
        children: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "Aria",
          applicationCategory: "HealthApplication",
          operatingSystem: "iOS, Android, Web",
          description,
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        }),
      },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <div className="relative min-h-screen overflow-x-clip">
      <Nav />
      <main>
        <Hero />
        <TrustedBy />
        <Suspense fallback={<div className="h-40" />}>
          <Features />
          <HowItWorks />
          <div className="relative">
            <Blobs className="opacity-60" />
            <JourneyTimeline />
            <CompanionShowcase />
          </div>
          <Personalization />
          <Privacy />
          <Testimonials />
          <Faq />
          <Waitlist />
        </Suspense>
      </main>
      <Suspense fallback={null}>
        <Footer />
      </Suspense>
    </div>
  );
}
